"""Main Textual application."""

import asyncio
import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Input, Tree
from textual.binding import Binding
from textual.message import Message

from src.ui.widgets.chat_pane import ChatPane
from src.ui.widgets.sidebar import Sidebar, MemberList
from src.ui.widgets.channel_search import ChannelSearchScreen
from src.ui.screens import TeletextScreen, HomeScreen
from src.core.irc_client import IRCClient
from src.core.mcp_client import MCPClient
from src.core.wormhole import WormholeClient
from src.core.audio import AudioEngine


class MemberListUpdate(Message):
    """Message to update member list."""
    def __init__(self, channel: str, members: list[str]):
        super().__init__()
        self.channel = channel
        self.members = members


class ConnectionStatus(Message):
    """Message to update connection status."""
    def __init__(self, connected: bool, status: str = ""):
        super().__init__()
        self.connected = connected
        self.status = status


class CordTUI(App):
    """The main Cord-TUI application."""
    
    CSS_PATH = "styles.tcss"
    TITLE = "Cord-TUI"
    
    BINDINGS = [
        Binding("f1", "toggle_teletext", "Teletext", show=True),
        Binding("ctrl+j", "search_channels", "Join Channel", show=True),
        Binding("ctrl+c", "quit", "Quit", show=True),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = self._load_config()
        self.current_channel = "#general"
        self.irc_connected = False
        self.connection_status = "disconnected"  # disconnected, connecting, connected
        self.channels_joined = set()  # Track which channels we've successfully joined
        self.irc = None
        self.mcp = MCPClient()
        self.wormhole = WormholeClient()
        self.audio = None
        self.input_bar = None
        self.chat_pane = None
        
        # Set up wormhole callback
        self.wormhole.set_status_callback(self._on_wormhole_status)
    
    def _load_config(self) -> dict:
        """Load configuration from .cord/config.json."""
        config_path = Path(".cord/config.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}
    
    def compose(self) -> ComposeResult:
        """Compose the main UI layout."""
        yield Header()
        
        with Horizontal():
            # Left sidebar - channels
            channels = self.config["servers"][0]["channels"]
            yield Sidebar(channels, id="sidebar")
            
            # Center - chat pane
            with Container(id="chat-container"):
                yield ChatPane(id="chat-pane")
                yield Input(
                    placeholder=f"Message {self.current_channel}",
                    id="input-bar"
                )
            
            # Right sidebar - members
            yield MemberList(id="member-list")
        
        yield Footer()
    
    async def on_mount(self):
        """Show home screen first."""
        self.push_screen(HomeScreen(config=self.config))

    def on_home_screen_settings_confirmed(self, event: HomeScreen.SettingsConfirmed):
        """Handle settings from home screen."""
        # Update config with user settings
        self.config["servers"][0]["nick"] = event.nick
        self.config["audio"]["enabled"] = event.audio_enabled
        self.config["audio"]["volume"] = event.volume
        
        # Initialize IRC client with chosen nick
        server = self.config["servers"][0]
        self.irc = IRCClient(
            host=server["host"],
            port=server["port"],
            nick=event.nick,
            ssl=server["ssl"]
        )
        self.irc.set_message_callback(self._on_irc_message)
        self.irc.set_members_callback(self._on_members_update)
        self.irc.set_channel_list_callback(self._on_channel_list_received)
        
        # Initialize audio with chosen settings
        self.audio = AudioEngine(
            enabled=event.audio_enabled,
            volume=event.volume
        )
        
        # Pop home screen and start main app
        self.pop_screen()
        self._start_main_app()

    def _start_main_app(self):
        """Initialize the main app after home screen."""
        self.chat_pane = self.query_one("#chat-pane", ChatPane)
        self.input_bar = self.query_one("#input-bar", Input)
        self.member_list = self.query_one("#member-list", MemberList)
        
        # Set initial channel in chat pane
        self.chat_pane.current_channel = self.current_channel
        
        # Set initial placeholder
        self.input_bar.placeholder = "Connecting to IRC..."
        
        # Welcome message
        self.chat_pane.add_message("System", f"Welcome to Cord-TUI, {self.irc.nick}! 🚀", is_system=True)
        self.chat_pane.add_message("System", "Press F1 for Teletext Dashboard", is_system=True)
        
        # Connect to IRC in background
        asyncio.create_task(self._connect_irc())
    
    async def _connect_irc(self):
        """Connect to IRC server."""
        try:
            self.connection_status = "connecting"
            self.chat_pane.add_message("System", f"Connecting to {self.irc.host}:{self.irc.port}...", is_system=True)
            
            # Check internet connectivity first
            try:
                import socket
                socket.create_connection((self.irc.host, self.irc.port), timeout=5)
            except (socket.error, OSError):
                self.chat_pane.add_message("System", "Device appears to be offline. Check internet connection.", is_system=True)
                self.connection_status = "offline"
                return
            
            await self.irc.connect()
            
            # Give it a moment to connect
            await asyncio.sleep(2)
            
            self.connection_status = "connected"
            self.irc_connected = True
            self.chat_pane.add_message("System", "✓ Connected to IRC!", is_system=True)
            
            # Join channels with loading indicators
            for channel in self.config["servers"][0]["channels"]:
                self.chat_pane.add_message("System", f"Joining {channel}...", is_system=True)
                self.irc.join_channel(channel)
                
                # Wait a bit for the join to complete
                await asyncio.sleep(1)
                
                # Mark as joined (we'll get confirmation via IRC events)
                self.channels_joined.add(channel)
                self.chat_pane.add_message("System", f"Joined {channel}", is_system=True)
            
            self.chat_pane.add_message("System", "Ready to chat! Select a channel and start messaging.", is_system=True)
            
            # Update input placeholder
            if self.current_channel in self.channels_joined:
                self.input_bar.placeholder = f"Message {self.current_channel}"
            else:
                self.input_bar.placeholder = "Select a channel to start chatting"
            
        except Exception as e:
            self.chat_pane.add_message("System", f"IRC connection failed: {e}", is_system=True)
            self.chat_pane.add_message("System", "Check your internet connection and try restarting.", is_system=True)
            self.connection_status = "failed"
            self.irc_connected = False
    
    def _on_irc_message(self, nick: str, target: str, message: str):
        """Handle incoming IRC messages."""
        # target is the channel the message was sent to
        # miniirc runs in a separate thread, so we need call_from_thread
        self.call_from_thread(self.chat_pane.add_message, nick, message, False, target)
        self.audio.process_log(message)
    
    def _on_members_update(self, channel: str, members: list[str]):
        """Handle member list updates."""
        # Only update if this is the current channel
        if channel == self.current_channel:
            # Use post_message for thread-safe UI updates
            self.post_message(MemberListUpdate(channel, members))
    
    def _on_channel_list_received(self, channels: list):
        """Handle channel list from IRC server."""
        # Debug: Add a system message to show we received channels
        self.call_from_thread(self.chat_pane.add_message, "System", f"DEBUG: Received {len(channels)} channels from IRC", True)
        
        # Forward to channel search screen if it's open
        if hasattr(self, '_channel_search_screen') and self._channel_search_screen:
            self.call_from_thread(self._channel_search_screen.update_channel_list, channels)
        else:
            self.call_from_thread(self.chat_pane.add_message, "System", "DEBUG: No channel search screen open", True)
    
    def _on_wormhole_status(self, status: str):
        """Handle wormhole status updates."""
        self.call_from_thread(self.chat_pane.add_message, "Wormhole", status, is_system=True)
    
    def on_member_list_update(self, event: MemberListUpdate):
        """Handle member list updates."""
        if event.channel == self.current_channel:
            self.member_list.update_members(event.members)
    
    def on_sidebar_channel_selected(self, event: Sidebar.ChannelSelected):
        """Handle channel selection from sidebar."""
        self.current_channel = event.channel
        
        # Update placeholder based on connection and channel status
        if not self.irc_connected:
            self.input_bar.placeholder = "Not connected to IRC"
        elif self.current_channel not in self.channels_joined:
            self.input_bar.placeholder = f"Joining {self.current_channel}..."
        else:
            self.input_bar.placeholder = f"Message {self.current_channel}"
        
        # Switch chat pane to show this channel's messages
        self.chat_pane.switch_channel(self.current_channel)
        self.chat_pane.add_message("System", f"Switched to {self.current_channel}", is_system=True)
        
        # Update member list for new channel
        members = self.irc.get_channel_members(self.current_channel)
        if members:
            self.member_list.update_members(members)
        else:
            # Show loading if no members yet
            self.member_list.show_loading(self.current_channel)
    
    async def on_input_submitted(self, event: Input.Submitted):
        """Handle message submission."""
        # Ignore if input_bar not yet initialized (e.g., from HomeScreen)
        if not hasattr(self, "input_bar") or self.input_bar is None:
            return
        
        message = event.value.strip()
        if not message:
            return
        
        self.input_bar.value = ""
        
        # Check if we're in a valid channel
        if not self.current_channel or not self.current_channel.startswith("#"):
            self.chat_pane.add_message("System", "Not in a channel. Select a channel first.", is_system=True)
            return
        
        # Check if we're connected
        if not self.irc_connected:
            self.chat_pane.add_message("System", "Not connected to IRC. Please wait for connection.", is_system=True)
            return
        
        # Check if we've joined this channel
        if self.current_channel not in self.channels_joined:
            self.chat_pane.add_message("System", f"Not joined to {self.current_channel}. Please wait...", is_system=True)
            return
        
        # Handle commands
        if message.startswith("/"):
            await self._handle_command(message)
        else:
            # Send to IRC
            try:
                self.irc.send_message(self.current_channel, message)
                # Add to current channel's history
                self.chat_pane.add_message("You", message, False, self.current_channel)
            except Exception as e:
                self.chat_pane.add_message("System", f"Failed to send: {e}", is_system=True)
    
    async def _handle_command(self, command: str):
        """Handle slash commands."""
        parts = command[1:].split(maxsplit=1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == "send":
            # Send file via wormhole
            self.chat_pane.add_message("System", f"Sending {args}...", is_system=True)
            code = await self.wormhole.send_file(args)
            self.chat_pane.add_embed(
                "File Transfer Ready",
                f"Code: `{code}`\n\nRecipient should run: `/grab {code}`",
                "success"
            )
        
        elif cmd == "grab":
            # Receive file via wormhole
            self.chat_pane.add_message("System", f"Receiving file with code {args}...", is_system=True)
            success = await self.wormhole.receive_file(args)
            if success:
                self.chat_pane.add_embed("File Received", "Transfer complete!", "success")
        
        elif cmd == "ai":
            # Execute MCP command
            self.chat_pane.add_message("System", f"Executing AI command: {args}", is_system=True)
            result = await self.mcp.execute(args)
            
            if "error" in result:
                self.chat_pane.add_embed("AI Error", result["error"], "error")
            elif "message" in result:
                # Plain text message (like help text)
                self.chat_pane.add_embed("AI Assistant", result["message"], "info")
            else:
                # Format result as JSON
                import json
                result_str = json.dumps(result, indent=2)
                self.chat_pane.add_embed("AI Result", f"```json\n{result_str}\n```", "success")
        
        elif cmd == "join":
            # Join or create channel
            if not args:
                self.action_search_channels()
            else:
                channel = args.strip()
                if not channel.startswith('#'):
                    channel = '#' + channel
                
                # Add to sidebar if not already there
                sidebar = self.query_one("#sidebar", Sidebar)
                if channel not in sidebar.channels:
                    sidebar.channels.append(channel)
                    # Refresh sidebar display
                    tree = sidebar.query_one(Tree)
                    tree.root.add_leaf(f"# {channel}", data=channel)
                
                # Join the channel
                self.irc.join_channel(channel)
                self.channels_joined.add(channel)
                
                # Switch to the new channel
                self.current_channel = channel
                self.chat_pane.switch_channel(self.current_channel)
                self.chat_pane.add_message("System", f"Joined {channel}", is_system=True)
                
                # Update UI
                self.input_bar.placeholder = f"Message {self.current_channel}"
                self.member_list.show_loading(channel)
        
        else:
            self.chat_pane.add_message("System", f"Unknown command: /{cmd}", is_system=True)
            self.chat_pane.add_message("System", "Available commands: /join, /send, /grab, /ai", is_system=True)
    
    def action_toggle_teletext(self):
        """Toggle the Teletext dashboard."""
        self.push_screen(TeletextScreen(app_ref=self))
    
    def action_search_channels(self):
        """Open channel search dialog."""
        if not self.irc_connected:
            self.chat_pane.add_message("System", "Not connected to IRC. Cannot search channels.", is_system=True)
            return
        
        self.chat_pane.add_message("System", "DEBUG: Opening channel search screen", True)
        self._channel_search_screen = ChannelSearchScreen()
        
        # Pass recent channels to the search screen
        recent_channels = list(self.channels_joined)
        self._channel_search_screen.recent_channels.update(recent_channels)
        
        self.push_screen(self._channel_search_screen)
    
    def request_channel_list(self, pattern: str = None):
        """Request channel list from IRC server."""
        self.chat_pane.add_message("System", f"DEBUG: request_channel_list called, connected: {self.irc_connected}", True)
        if self.irc_connected:
            self.chat_pane.add_message("System", f"DEBUG: Calling irc.list_channels with pattern: {pattern}", True)
            self.irc.list_channels(pattern)
        else:
            self.chat_pane.add_message("System", "DEBUG: Not connected to IRC", True)
    
    def on_channel_search_screen_channel_selected(self, event: ChannelSearchScreen.ChannelSelected):
        """Handle channel selection from search dialog."""
        channel = event.channel
        
        # Check if already joined
        if channel in self.channels_joined:
            # Just switch to the channel
            self.current_channel = channel
            self.chat_pane.switch_channel(self.current_channel)
            self.chat_pane.add_message("System", f"Switched to {channel}", is_system=True)
            self.input_bar.placeholder = f"Message {self.current_channel}"
            return
        
        # Add to sidebar if not already there
        sidebar = self.query_one("#sidebar", Sidebar)
        if channel not in sidebar.channels:
            sidebar.channels.append(channel)
            # Refresh sidebar display
            tree = sidebar.query_one(Tree)
            tree.root.add_leaf(f"# {channel}", data=channel)
        
        # Join the channel
        self.irc.join_channel(channel)
        self.channels_joined.add(channel)
        
        # Update recent channels in search screen for next time
        if hasattr(self, '_channel_search_screen'):
            self._channel_search_screen.add_recent_channel(channel)
        
        # Switch to the new channel
        self.current_channel = channel
        self.chat_pane.switch_channel(self.current_channel)
        self.chat_pane.add_message("System", f"Joined {channel}", is_system=True)
        
        # Update UI
        self.input_bar.placeholder = f"Message {self.current_channel}"
        self.member_list.show_loading(channel)
    
    async def on_unmount(self):
        """Clean up on exit."""
        if self.irc:
            await self.irc.disconnect()
