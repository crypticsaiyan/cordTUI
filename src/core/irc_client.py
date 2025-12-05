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
        self.original_nick = nick  # Store original requested nick
        self.ssl = ssl
        self.message_callback: Optional[Callable] = None
        self.members_callback: Optional[Callable] = None
        self.channel_list_callback: Optional[Callable] = None
        self.join_callback: Optional[Callable] = None  # Callback for successful joins
        self.nick_callback: Optional[Callable] = None  # Callback for nickname changes/confirmation
        self.channel_members = {}  # Track members per channel
        self._names_in_progress = set()  # Track which channels are receiving NAMES
        self._channel_list = []  # Store channel list from LIST command
        self.client = None
        self._thread = None
        self._nick_attempt = 0  # Track nickname attempts
        self._nick_confirmed = False  # Track if nick is confirmed
        self._max_nick_attempts = 99  # Max number suffix to try
        
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
                quit_message="Goodbye!",
                auto_connect=False  # Don't auto-connect, we'll do it explicitly
            )
            
            # Store client reference for access from other threads
            self.client = client
            
            # Set up handlers
            @client.Handler('PRIVMSG')
            def handle_privmsg(irc, hostmask, args):
                # Strip any IRC protocol artifacts (leading colons)
                nick = hostmask[0].lstrip(':')
                target = args[0].lstrip(':')
                message = args[1].lstrip(':') if len(args) > 1 else ""
                if self.message_callback:
                    self.message_callback(nick, target, message)
            
            @client.Handler('353', colon=False)  # RPL_NAMREPLY
            def handle_names(irc, hostmask, args):
                # miniirc format: args = ['yournick', '=', '#channel', 'nick1 nick2 nick3']
                if len(args) >= 4:
                    channel = args[2]
                    names_str = args[3].lstrip(':')  # Strip IRC protocol colon
                    names = names_str.split()
                    # Strip IRC prefixes (@, +, etc.) and any remaining colons
                    clean_names = [name.lstrip('@+%&~:') for name in names]
                    
                    if channel not in self._names_in_progress:
                        self._names_in_progress.add(channel)
                        self.channel_members[channel] = []
                    
                    self.channel_members[channel].extend(clean_names)
                elif len(args) >= 3:
                    channel = args[1] if args[0] in ('=', '*', '@') else args[0]
                    names_str = args[-1].lstrip(':')  # Strip IRC protocol colon
                    names = names_str.split()
                    # Strip IRC prefixes (@, +, etc.) and any remaining colons
                    clean_names = [name.lstrip('@+%&~:') for name in names]
                    
                    if channel not in self._names_in_progress:
                        self._names_in_progress.add(channel)
                        self.channel_members[channel] = []
                    
                    self.channel_members[channel].extend(clean_names)
            
            @client.Handler('366', colon=False)  # RPL_ENDOFNAMES
            def handle_names_end(irc, hostmask, args):
                if len(args) >= 2:
                    channel = args[1]
                    self._names_in_progress.discard(channel)
                    if self.members_callback and channel in self.channel_members:
                        self.members_callback(channel, self.channel_members[channel])
                    # Notify that channel join is complete
                    if self.join_callback:
                        self.join_callback(channel, True)
            
            @client.Handler('JOIN')
            def handle_join(irc, hostmask, args):
                nick = hostmask[0].lstrip(':')
                channel = args[0].lstrip(':')
                if channel not in self.channel_members:
                    self.channel_members[channel] = []
                if nick not in self.channel_members[channel]:
                    self.channel_members[channel].append(nick)
                    if self.members_callback:
                        self.members_callback(channel, self.channel_members[channel])
            
            @client.Handler('PART')
            def handle_part(irc, hostmask, args):
                nick = hostmask[0].lstrip(':')
                channel = args[0].lstrip(':')
                if channel in self.channel_members and nick in self.channel_members[channel]:
                    self.channel_members[channel].remove(nick)
                    if self.members_callback:
                        self.members_callback(channel, self.channel_members[channel])
            
            @client.Handler('QUIT')
            def handle_quit(irc, hostmask, args):
                nick = hostmask[0].lstrip(':')
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
            
            @client.Handler('433', colon=False)  # ERR_NICKNAMEINUSE - override miniirc's handler
            def handle_nick_in_use(irc, hostmask, args):
                """Handle nickname already in use - try with random number suffix."""
                import random
                print(f"[IRC DEBUG] Nickname in use: {args}")
                self._nick_attempt += 1
                if self._nick_attempt <= self._max_nick_attempts:
                    # Generate random 3-4 digit number
                    random_suffix = random.randint(100, 9999)
                    new_nick = f"{self.original_nick}{random_suffix}"
                    # Truncate if too long (IRC max is usually 30)
                    if len(new_nick) > 30:
                        suffix = str(random_suffix)
                        max_base = 30 - len(suffix)
                        new_nick = f"{self.original_nick[:max_base]}{suffix}"
                    print(f"[IRC DEBUG] Trying new nick: {new_nick}")
                    self.nick = new_nick
                    # Update miniirc's internal nick tracking to prevent it from
                    # trying its own nick collision handling (appending '_')
                    irc._current_nick = new_nick
                    irc._desired_nick = new_nick
                    irc._keepnick_active = False  # Don't try to reclaim original nick
                    irc.quote('NICK', new_nick, force=True)
                else:
                    print(f"[IRC DEBUG] Max nick attempts reached")
                    if self.nick_callback:
                        self.nick_callback(None, False, "Could not find available nickname")
            
            @client.Handler('001')  # RPL_WELCOME - nickname confirmed
            def handle_welcome(irc, hostmask, args):
                """Handle welcome message - nickname is now confirmed."""
                # The first arg after our nick in 001 is usually the welcome message
                # miniirc sets _current_nick from the 001 response
                confirmed_nick = irc._current_nick if hasattr(irc, '_current_nick') and irc._current_nick else self.nick
                # Strip any IRC protocol artifacts
                confirmed_nick = confirmed_nick.lstrip(':')
                print(f"[IRC DEBUG] Welcome received, nick confirmed: {confirmed_nick}, our tracking: {self.nick}")
                
                # Ensure all nick tracking is in sync
                self.nick = confirmed_nick
                self._nick_confirmed = True
                
                if self.nick_callback:
                    changed = confirmed_nick != self.original_nick
                    self.nick_callback(confirmed_nick, True, "connected" if not changed else f"nickname changed to {confirmed_nick}")
            
            @client.Handler('NICK')
            def handle_nick_change(irc, hostmask, args):
                """Handle nickname changes (including our own)."""
                old_nick = hostmask[0].lstrip(':')
                new_nick = (args[0] if args else old_nick).lstrip(':')
                print(f"[IRC DEBUG] Nick change: {old_nick} -> {new_nick}")
                # If it's our nick changing, update it
                if old_nick == self.nick or old_nick == self.original_nick:
                    self.nick = new_nick
                    if self.nick_callback:
                        self.nick_callback(new_nick, True, f"nickname changed to {new_nick}")
                # Update in channel member lists
                for channel in self.channel_members:
                    if old_nick in self.channel_members[channel]:
                        self.channel_members[channel].remove(old_nick)
                        self.channel_members[channel].append(new_nick)
                        if self.members_callback:
                            self.members_callback(channel, self.channel_members[channel])
            
            # Sync our nick property with miniirc's current_nick periodically
            @client.Handler('PING')
            def handle_ping_sync(irc, hostmask, args):
                """Sync nick on PING to ensure we stay in sync with server."""
                if hasattr(irc, 'current_nick') and irc.current_nick and irc.current_nick != self.nick:
                    print(f"[IRC DEBUG] Nick sync: {self.nick} -> {irc.current_nick}")
                    self.nick = irc.current_nick
            
            # Start the client (this blocks)
            client.connect()
        
        # Run in a separate thread
        self._thread = threading.Thread(target=run_client, daemon=True)
        self._thread.start()
        
        # Don't block here - let the app poll for client readiness
        await asyncio.sleep(0.1)
    
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
    
    def set_join_callback(self, callback: Callable):
        """Set callback for channel join completion."""
        self.join_callback = callback
    
    def set_nick_callback(self, callback: Callable):
        """Set callback for nickname changes/confirmation.
        
        Callback signature: callback(nick: str, success: bool, message: str)
        - nick: The confirmed/new nickname (or None if failed)
        - success: True if nick is confirmed, False if failed
        - message: Status message
        """
        self.nick_callback = callback
    
    def is_nick_confirmed(self) -> bool:
        """Check if nickname has been confirmed by server."""
        return self._nick_confirmed
    
    def get_confirmed_nick(self) -> str:
        """Get the server-confirmed nickname."""
        # Prefer miniirc's current_nick as it's the authoritative source
        if self.client and hasattr(self.client, 'current_nick') and self.client.current_nick:
            return self.client.current_nick
        return self.nick
    
    def change_nick(self, new_nick: str):
        """Request a nickname change."""
        if self.client:
            self.client.send('NICK', new_nick)
    
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
