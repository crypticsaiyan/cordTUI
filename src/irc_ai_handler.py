#!/usr/bin/env python3
"""
IRC AI Handler - Listens for /ai commands and responds with Azure container info
"""

import miniirc
import time
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from src.azure_container_manager import AzureContainerManager


class IRCAIHandler:
    """Handles /ai commands in IRC with rate limiting and error handling"""
    
    def __init__(self, azure_manager: AzureContainerManager, 
                 cooldown_seconds: int = 10):
        """
        Initialize IRC AI Handler
        
        Args:
            azure_manager: AzureContainerManager instance
            cooldown_seconds: Cooldown period per user
        """
        self.azure_manager = azure_manager
        self.cooldown_seconds = cooldown_seconds
        
        # Rate limiting: track last command time per user
        self.user_last_command: Dict[str, datetime] = {}
        
        # Track processing state
        self.processing = False
        
    def is_rate_limited(self, user: str) -> bool:
        """Check if user is rate limited"""
        if user not in self.user_last_command:
            return False
        
        time_since_last = datetime.now() - self.user_last_command[user]
        return time_since_last.seconds < self.cooldown_seconds
    
    def get_cooldown_remaining(self, user: str) -> int:
        """Get remaining cooldown time for user"""
        if user not in self.user_last_command:
            return 0
        
        time_since_last = datetime.now() - self.user_last_command[user]
        remaining = self.cooldown_seconds - time_since_last.seconds
        return max(0, remaining)
    
    def handle_ai_command(self, irc: miniirc.IRC, hostmask: tuple, 
                         args: list) -> None:
        """
        Handle /ai command from IRC
        
        Args:
            irc: miniirc IRC instance
            hostmask: (nick, ident, host) tuple
            args: [channel, message]
        """
        nick = hostmask[0]
        channel = args[0]
        message = args[1]
        
        # Check if message starts with /ai
        if not message.strip().startswith('/ai '):
            return
        
        # Extract question
        question = message.strip()[4:].strip()
        
        if not question:
            irc.msg(channel, f"{nick}: Usage: /ai <your question>")
            return
        
        # Rate limiting check
        if self.is_rate_limited(nick):
            remaining = self.get_cooldown_remaining(nick)
            irc.msg(channel, f"{nick}: Please wait {remaining}s before next query.")
            return
        
        # Prevent concurrent processing
        if self.processing:
            irc.msg(channel, f"{nick}: Processing another query, please wait...")
            return
        
        try:
            self.processing = True
            self.user_last_command[nick] = datetime.now()
            
            # Send processing message
            irc.msg(channel, f"🤖 Processing query from {nick}...")
            
            # Get answer from Azure
            answer = self.azure_manager.answer_question(question)
            
            # Split long messages
            self._send_multiline(irc, channel, f"💡 {answer}")
            
        except Exception as e:
            error_msg = "I can't reach Azure right now — try again later."
            print(f"Error processing AI command: {e}")
            irc.msg(channel, f"❌ {error_msg}")
            
        finally:
            self.processing = False
    
    def _send_multiline(self, irc: miniirc.IRC, channel: str, 
                       message: str, max_length: int = 400) -> None:
        """
        Send long messages split into multiple lines
        
        Args:
            irc: miniirc IRC instance
            channel: Target channel
            message: Message to send
            max_length: Maximum length per message
        """
        lines = message.split('\n')
        
        for line in lines:
            if len(line) <= max_length:
                irc.msg(channel, line)
                time.sleep(0.5)  # Avoid flooding
            else:
                # Split long lines
                chunks = [line[i:i+max_length] for i in range(0, len(line), max_length)]
                for chunk in chunks:
                    irc.msg(channel, chunk)
                    time.sleep(0.5)


class IRCAIBot:
    """Main IRC bot with AI capabilities"""
    
    def __init__(self, server: str, port: int, nick: str, 
                 channels: list, azure_manager: AzureContainerManager,
                 use_ssl: bool = False):
        """
        Initialize IRC AI Bot
        
        Args:
            server: IRC server address
            port: IRC server port
            nick: Bot nickname
            channels: List of channels to join
            azure_manager: AzureContainerManager instance
            use_ssl: Use SSL connection
        """
        self.server = server
        self.port = port
        self.nick = nick
        self.channels = channels
        self.azure_manager = azure_manager
        self.use_ssl = use_ssl
        
        # Initialize AI handler
        self.ai_handler = IRCAIHandler(azure_manager)
        
        # Initialize IRC connection
        self.irc = miniirc.IRC(
            ip=server,
            port=port,
            nick=nick,
            channels=channels,
            ssl=use_ssl,
            debug=False
        )
        
        # Register message handler
        @self.irc.Handler('PRIVMSG')
        def handle_privmsg(irc, hostmask, args):
            self.ai_handler.handle_ai_command(irc, hostmask, args)
        
        # Connection status handlers
        @self.irc.Handler('001')  # Welcome message
        def handle_welcome(irc, hostmask, args):
            print(f"✅ Connected to {server} as {nick}")
            print(f"📢 Joined channels: {', '.join(channels)}")
            print(f"🤖 AI bot ready! Users can type: /ai <question>")
        
        @self.irc.Handler('JOIN')
        def handle_join(irc, hostmask, args):
            if hostmask[0] == nick:
                print(f"✅ Joined {args[0]}")
    
    def run(self):
        """Start the bot (blocking)"""
        print(f"🚀 Starting IRC AI Bot...")
        print(f"   Server: {self.server}:{self.port}")
        print(f"   Nick: {self.nick}")
        print(f"   Channels: {', '.join(self.channels)}")
        print(f"   SSL: {self.use_ssl}")
        print()
        
        try:
            # Keep bot running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down bot...")
            self.irc.disconnect()
