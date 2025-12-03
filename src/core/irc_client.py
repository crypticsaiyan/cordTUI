"""IRC client wrapper using miniirc library."""

import asyncio
import miniirc
from typing import Callable, Optional
import threading


class IRCClient:
    """Async IRC client wrapper using miniirc."""
    
    def __init__(self, host: str, port: int, nick: str, ssl: bool = False):
        self.host = host
        self.port = port
        self.nick = nick
        self.ssl = ssl
        self.message_callback: Optional[Callable] = None
        self.members_callback: Optional[Callable] = None
        self.channel_list_callback: Optional[Callable] = None
        self.channel_members = {}  # Track members per channel
        self._names_in_progress = set()  # Track which channels are receiving NAMES
        self._channel_list = []  # Store channel list from LIST command
        self.client = None
        self._thread = None
        
    async def connect(self):
        """Connect to IRC server."""
        # miniirc runs in its own thread
        def run_client():
            client = miniirc.IRC(
                ip=self.host,
                port=self.port,
                nick=self.nick,
                channels=[],  # We'll join manually
                ssl=self.ssl,
                debug=False,
                ns_identity=None,
                connect_modes=None,
                quit_message="Goodbye!"
            )
            
            # Store client reference for access from other threads
            self.client = client
            
            # Set up handlers
            @client.Handler('PRIVMSG')
            def handle_privmsg(irc, hostmask, args):
                nick = hostmask[0]
                target = args[0]
                message = args[1]
                if self.message_callback:
                    self.message_callback(nick, target, message)
            
            @client.Handler('353')  # RPL_NAMREPLY
            def handle_names(irc, hostmask, args):
                # args: [nick, '=', '#channel', ':user1 user2 user3']
                if len(args) >= 4:
                    channel = args[2]
                    # Remove leading : from the names string
                    names_str = args[3].lstrip(':')
                    names = names_str.split()
                    # Remove mode prefixes (@, +, etc.)
                    clean_names = [name.lstrip('@+%&~:') for name in names]
                    
                    # If this is the first 353 for this channel, clear the list
                    if channel not in self._names_in_progress:
                        self._names_in_progress.add(channel)
                        self.channel_members[channel] = []
                    
                    # Extend the list (NAMES can come in multiple 353 messages for large channels)
                    self.channel_members[channel].extend(clean_names)
            
            @client.Handler('366')  # RPL_ENDOFNAMES
            def handle_names_end(irc, hostmask, args):
                # args: [nick, '#channel', 'End of /NAMES list']
                if len(args) >= 2:
                    channel = args[1]
                    # Mark NAMES as complete for this channel
                    self._names_in_progress.discard(channel)
                    if self.members_callback and channel in self.channel_members:
                        self.members_callback(channel, self.channel_members[channel])
            
            @client.Handler('JOIN')
            def handle_join(irc, hostmask, args):
                nick = hostmask[0]
                channel = args[0]
                if channel not in self.channel_members:
                    self.channel_members[channel] = []
                if nick not in self.channel_members[channel]:
                    self.channel_members[channel].append(nick)
                    if self.members_callback:
                        self.members_callback(channel, self.channel_members[channel])
            
            @client.Handler('PART')
            def handle_part(irc, hostmask, args):
                nick = hostmask[0]
                channel = args[0]
                if channel in self.channel_members and nick in self.channel_members[channel]:
                    self.channel_members[channel].remove(nick)
                    if self.members_callback:
                        self.members_callback(channel, self.channel_members[channel])
            
            @client.Handler('QUIT')
            def handle_quit(irc, hostmask, args):
                nick = hostmask[0]
                # Remove from all channels
                for channel in self.channel_members:
                    if nick in self.channel_members[channel]:
                        self.channel_members[channel].remove(nick)
                if self.members_callback:
                    for channel in self.channel_members:
                        self.members_callback(channel, self.channel_members[channel])
            
            @client.Handler('322')  # RPL_LIST
            def handle_list(irc, hostmask, args):
                """Handle channel list entry."""
                print(f"[IRC DEBUG] RPL_LIST received: {args}")
                # args: [nick, '#channel', 'user_count', ':topic']
                if len(args) >= 4:
                    channel = args[1]
                    user_count = int(args[2]) if args[2].isdigit() else 0
                    topic = args[3].lstrip(':') if len(args) > 3 else ""
                    self._channel_list.append({
                        'name': channel,
                        'users': user_count,
                        'topic': topic
                    })
                    print(f"[IRC DEBUG] Added channel: {channel} ({user_count} users)")
            
            @client.Handler('323')  # RPL_LISTEND
            def handle_list_end(irc, hostmask, args):
                """Handle end of channel list."""
                print(f"[IRC DEBUG] RPL_LISTEND received, {len(self._channel_list)} channels total")
                if self.channel_list_callback:
                    print(f"[IRC DEBUG] Calling callback with {len(self._channel_list)} channels")
                    self.channel_list_callback(self._channel_list.copy())
                else:
                    print("[IRC DEBUG] No callback set!")
                self._channel_list.clear()
            
            # Debug: catch LIST-related errors
            @client.Handler('263')  # RPL_TRYAGAIN
            def handle_try_again(irc, hostmask, args):
                print(f"[IRC DEBUG] Server says try again: {args}")
            
            @client.Handler('481')  # ERR_NOPRIVILEGES  
            def handle_no_privileges(irc, hostmask, args):
                print(f"[IRC DEBUG] No privileges error: {args}")
            
            @client.Handler('421')  # ERR_UNKNOWNCOMMAND
            def handle_unknown_command(irc, hostmask, args):
                print(f"[IRC DEBUG] Unknown command error: {args}")
            
            # Start the client (this blocks)
            client.connect()
        
        # Run in a separate thread
        self._thread = threading.Thread(target=run_client, daemon=True)
        self._thread.start()
        
        # Wait a bit for connection
        await asyncio.sleep(2)
    
    def join_channel(self, channel: str):
        """Join a channel."""
        if self.client:
            # Don't initialize here - let NAMES reply populate it
            self.client.send('JOIN', channel)
    
    def send_message(self, target: str, message: str):
        """Send a message to a channel or user."""
        if self.client:
            self.client.msg(target, message)
    
    def set_message_callback(self, callback: Callable):
        """Set callback for incoming messages."""
        self.message_callback = callback
    
    def set_members_callback(self, callback: Callable):
        """Set callback for member list updates."""
        self.members_callback = callback
    
    def set_channel_list_callback(self, callback: Callable):
        """Set callback for channel list updates."""
        self.channel_list_callback = callback
    
    def get_channel_members(self, channel: str) -> list[str]:
        """Get list of members in a channel."""
        return self.channel_members.get(channel, [])
    
    def list_channels(self, pattern: str = None):
        """Request channel list from server."""
        print(f"[IRC DEBUG] list_channels called with pattern: {pattern}")
        if self.client:
            try:
                if pattern:
                    print(f"[IRC DEBUG] Sending LIST with pattern: {pattern}")
                    # Try different formats for LIST command
                    self.client.send('LIST', pattern)
                else:
                    print("[IRC DEBUG] Sending LIST command (no pattern)")
                    # Send LIST without any parameters
                    self.client.send('LIST')
                print("[IRC DEBUG] LIST command sent successfully")
            except Exception as e:
                print(f"[IRC DEBUG] Error sending LIST: {e}")
        else:
            print("[IRC DEBUG] No client available")
    
    async def disconnect(self):
        """Disconnect from IRC server."""
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass
