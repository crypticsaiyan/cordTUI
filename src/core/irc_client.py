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
        self.channel_members = {}  # Track members per channel
        self._names_in_progress = set()  # Track which channels are receiving NAMES
        self.client = None
        self._thread = None
        
    async def connect(self):
        """Connect to IRC server."""
        # miniirc runs in its own thread
        def run_client():
            self.client = miniirc.IRC(
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
            
            # Set up handlers
            @self.client.Handler('PRIVMSG')
            def handle_privmsg(irc, hostmask, args):
                nick = hostmask[0]
                target = args[0]
                message = args[1]
                if self.message_callback:
                    self.message_callback(nick, target, message)
            
            @self.client.Handler('353')  # RPL_NAMREPLY
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
            
            @self.client.Handler('366')  # RPL_ENDOFNAMES
            def handle_names_end(irc, hostmask, args):
                # args: [nick, '#channel', 'End of /NAMES list']
                if len(args) >= 2:
                    channel = args[1]
                    # Mark NAMES as complete for this channel
                    self._names_in_progress.discard(channel)
                    if self.members_callback and channel in self.channel_members:
                        self.members_callback(channel, self.channel_members[channel])
            
            @self.client.Handler('JOIN')
            def handle_join(irc, hostmask, args):
                nick = hostmask[0]
                channel = args[0]
                if channel not in self.channel_members:
                    self.channel_members[channel] = []
                if nick not in self.channel_members[channel]:
                    self.channel_members[channel].append(nick)
                    if self.members_callback:
                        self.members_callback(channel, self.channel_members[channel])
            
            @self.client.Handler('PART')
            def handle_part(irc, hostmask, args):
                nick = hostmask[0]
                channel = args[0]
                if channel in self.channel_members and nick in self.channel_members[channel]:
                    self.channel_members[channel].remove(nick)
                    if self.members_callback:
                        self.members_callback(channel, self.channel_members[channel])
            
            @self.client.Handler('QUIT')
            def handle_quit(irc, hostmask, args):
                nick = hostmask[0]
                # Remove from all channels
                for channel in self.channel_members:
                    if nick in self.channel_members[channel]:
                        self.channel_members[channel].remove(nick)
                if self.members_callback:
                    for channel in self.channel_members:
                        self.members_callback(channel, self.channel_members[channel])
            
            # Start the client (this blocks)
            self.client.connect()
        
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
    
    def get_channel_members(self, channel: str) -> list[str]:
        """Get list of members in a channel."""
        return self.channel_members.get(channel, [])
    
    async def disconnect(self):
        """Disconnect from IRC server."""
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass
