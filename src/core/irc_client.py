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
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup IRC event handlers."""
        
        @self.client.on('CLIENT_CONNECT')
        async def on_connect(**kwargs):
            self.client.send('NICK', nick=self.nick)
            self.client.send('USER', user=self.nick, realname=self.nick)
        
        @self.client.on('PING')
        def on_ping(message, **kwargs):
            self.client.send('PONG', message=message)
        
        @self.client.on('PRIVMSG')
        def on_message(nick, target, message, **kwargs):
            if self.message_callback:
                self.message_callback(nick, target, message)
    
    async def connect(self):
        """Connect to IRC server."""
        await self.client.connect()
    
    def join_channel(self, channel: str):
        """Join a channel."""
        self.client.send('JOIN', channel=channel)
    
    def send_message(self, target: str, message: str):
        """Send a message to a channel or user."""
        self.client.send('PRIVMSG', target=target, message=message)
    
    def set_message_callback(self, callback: Callable):
        """Set callback for incoming messages."""
        self.message_callback = callback
    
    async def disconnect(self):
        """Disconnect from IRC server."""
        try:
            self.client.send('QUIT')
            await self.client.disconnect()
        except Exception:
            pass  # Ignore disconnect errors
