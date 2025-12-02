"""IRC client wrapper using bottom library."""

import asyncio
import bottom
from typing import Callable, Optional


class IRCClient:
    """Async IRC client wrapper."""
    
    def __init__(self, host: str, port: int, nick: str, ssl: bool = False):
        self.host = host
        self.port = port
        self.nick = nick
        self.ssl = ssl
        self.client = bottom.Client(host=host, port=port, ssl=ssl)
        self.message_callback: Optional[Callable] = None
        self.members_callback: Optional[Callable] = None
        self.channel_members = {}  # Track members per channel
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup IRC event handlers."""
        
        @self.client.on('CLIENT_CONNECT')
        def on_connect(**kwargs):
            asyncio.create_task(self.client.send('NICK', nick=self.nick))
            asyncio.create_task(self.client.send('USER', nick=self.nick, mode='0', realname=self.nick))
        
        @self.client.on('PING')
        def on_ping(message, **kwargs):
            asyncio.create_task(self.client.send('PONG', message=message))
        
        @self.client.on('PRIVMSG')
        def on_message(nick, target, message, **kwargs):
            print(f"[DEBUG] PRIVMSG received: nick={nick}, target={target}, message={message}")
            if self.message_callback:
                print(f"[DEBUG] Calling message_callback")
                self.message_callback(nick, target, message)
            else:
                print(f"[DEBUG] No message_callback set!")
        
        @self.client.on('RPL_NAMREPLY')
        def on_names(params, **kwargs):
            """Handle NAMES reply (353) - list of users in channel."""
            # params format: ['nick', '=', '#channel', 'user1 user2 user3']
            if len(params) >= 4:
                channel = params[2]
                names = params[3].split()
                # Remove mode prefixes (@, +, etc.)
                clean_names = [name.lstrip('@+%&~') for name in names]
                
                if channel not in self.channel_members:
                    self.channel_members[channel] = []
                self.channel_members[channel].extend(clean_names)
        
        @self.client.on('RPL_ENDOFNAMES')
        def on_names_end(params, **kwargs):
            """Handle end of NAMES list (366)."""
            # params format: ['nick', '#channel', 'End of /NAMES list']
            if len(params) >= 2:
                channel = params[1]
                if self.members_callback and channel in self.channel_members:
                    self.members_callback(channel, self.channel_members[channel])
        
        @self.client.on('JOIN')
        def on_join(nick, channel, **kwargs):
            """Handle user joining channel."""
            if channel not in self.channel_members:
                self.channel_members[channel] = []
            if nick not in self.channel_members[channel]:
                self.channel_members[channel].append(nick)
                if self.members_callback:
                    self.members_callback(channel, self.channel_members[channel])
        
        @self.client.on('PART')
        def on_part(nick, channel, **kwargs):
            """Handle user leaving channel."""
            if channel in self.channel_members and nick in self.channel_members[channel]:
                self.channel_members[channel].remove(nick)
                if self.members_callback:
                    self.members_callback(channel, self.channel_members[channel])
        
        @self.client.on('QUIT')
        def on_quit(nick, **kwargs):
            """Handle user quitting IRC."""
            # Remove from all channels
            for channel in self.channel_members:
                if nick in self.channel_members[channel]:
                    self.channel_members[channel].remove(nick)
            if self.members_callback:
                # Notify for all channels
                for channel in self.channel_members:
                    self.members_callback(channel, self.channel_members[channel])
        
        # Debug: catch all events
        @self.client.on('*')
        def on_any_event(event, **kwargs):
            print(f"[DEBUG] IRC Event: {event}")
    
    async def connect(self):
        """Connect to IRC server."""
        # Connect and keep the loop running in background
        await self.client.connect()
        # The client needs to keep running to process events
        # We don't await this so it runs in the background
        self._loop_task = asyncio.create_task(self._keep_alive())
    
    def join_channel(self, channel: str):
        """Join a channel."""
        # Initialize member list for this channel
        self.channel_members[channel] = []
        asyncio.create_task(self.client.send('JOIN', channel=channel))
    
    def send_message(self, target: str, message: str):
        """Send a message to a channel or user."""
        asyncio.create_task(self.client.send('PRIVMSG', target=target, message=message))
    
    def set_message_callback(self, callback: Callable):
        """Set callback for incoming messages."""
        self.message_callback = callback
    
    def set_members_callback(self, callback: Callable):
        """Set callback for member list updates."""
        self.members_callback = callback
    
    def get_channel_members(self, channel: str) -> list[str]:
        """Get list of members in a channel."""
        return self.channel_members.get(channel, [])
    
    async def _keep_alive(self):
        """Keep the client loop running to process events."""
        try:
            # Wait until disconnected
            await self.client.wait('CLIENT_DISCONNECT')
        except Exception as e:
            print(f"[DEBUG] Keep-alive loop ended: {e}")
    
    async def disconnect(self):
        """Disconnect from IRC server."""
        try:
            await self.client.send('QUIT')
            await self.client.disconnect()
        except Exception:
            pass  # Ignore disconnect errors
