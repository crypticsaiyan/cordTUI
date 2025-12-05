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
        Binding("ctrl+b", "toggle_bookmark", "Bookmark", show=True),
        Binding("ctrl+c", "quit", "Quit", show=True),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = self._load_config()
        self.bookmarks = self._load_bookmarks()
        self.current_channel = "#general"
        self.irc_connected = False
        self.connection_status = "disconnected"  # disconnected, connecting, connected
        self.channels_joined = set()  # Track which channels we've successfully joined
        self.channels_joining = set()  # Track which channels are currently joining
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
    
    def _load_bookmarks(self) -> list[str]:
        """Load bookmarked channels from .cord/bookmarks.json."""
        bookmarks_path = Path(".cord/bookmarks.json")
        if bookmarks_path.exists():
            try:
                with open(bookmarks_path) as f:
                    data = json.load(f)
                    return data.get("channels", [])
            except Exception:
                return []
        return []
    
    def _save_bookmarks(self):
        """Save bookmarked channels to .cord/bookmarks.json."""
        bookmarks_path = Path(".cord/bookmarks.json")
        bookmarks_path.parent.mkdir(exist_ok=True)
        try:
            with open(bookmarks_path, 'w') as f:
                json.dump({"channels": self.bookmarks}, f, indent=2)
        except Exception as e:
            if self.chat_pane:
                self.chat_pane.add_message("System", f"Failed to save bookmarks: {e}", is_system=True)
    
    def compose(self) -> ComposeResult:
        """Compose the main UI layout."""
        yield Header()
        
        with Horizontal():
            # Left sidebar - channels (will be updated after server selection)
            default_channels = self.config.get("servers", [{}])[0].get("channels", [])
            yield Sidebar(default_channels, bookmarked_channels=self.bookmarks, id="sidebar")
            
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
        # Use the selected server from the event
        server = event.server
        
        # Update config with user settings
        self.config["audio"]["enabled"] = event.audio_enabled
        self.config["audio"]["volume"] = event.volume
        
        # Store selected server config for later use
        self.selected_server = server
        
        # Initialize IRC client with chosen server and nick
        self.irc = IRCClient(
            host=server["host"],
            port=server["port"],
            nick=event.nick,
            ssl=server.get("ssl", False)
        )
        self.irc.set_message_callback(self._on_irc_message)
        self.irc.set_members_callback(self._on_members_update)
        self.irc.set_channel_list_callback(self._on_channel_list_received)
        self.irc.set_join_callback(self._on_channel_joined)
        
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
        
        # Update sidebar with selected server's channels and bookmarks
        sidebar = self.query_one("#sidebar", Sidebar)
        server_channels = self.selected_server.get("channels", [])
        sidebar.bookmarked_channels = self.bookmarks
        sidebar.update_channels(server_channels)
        
        # Set initial channel from server config
        if server_channels:
            self.current_channel = server_channels[0]
        
        # Set initial channel in chat pane
        self.chat_pane.current_channel = self.current_channel
        
        # Set initial placeholder
        self.input_bar.placeholder = "Connecting to IRC..."
        
        # Welcome message
        server_name = self.selected_server.get("name", self.selected_server.get("host"))
        self.chat_pane.add_message("System", f"Welcome to Cord-TUI, {self.irc.nick}! 🚀", is_system=True)
        self.chat_pane.add_message("System", f"Connecting to {server_name}...", is_system=True)
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
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((self.irc.host, self.irc.port))
                sock.close()
                self.chat_pane.add_message("System", "✓ Network connectivity verified", is_system=True)
            except (socket.error, OSError, socket.timeout) as e:
                self.chat_pane.add_message("System", f"❌ Cannot reach {self.irc.host}:{self.irc.port}", is_system=True)
                self.chat_pane.add_message("System", "Device appears to be offline. Check internet connection.", is_system=True)
                self.connection_status = "offline"
                self.input_bar.placeholder = "Offline - Check connection"
                return
            
            await self.irc.connect()
            
            # Give it a moment to connect
            await asyncio.sleep(2)
            
            self.connection_status = "connected"
            self.irc_connected = True
            self.chat_pane.add_message("System", "✓ Connected to IRC!", is_system=True)
            
            # Join channels with loading indicators
            server_channels = self.selected_server.get("channels", [])
            for channel in server_channels:
                self.chat_pane.add_message("System", f"Joining {channel}...", is_system=True)
                self.channels_joining.add(channel)
                self.irc.join_channel(channel)
            
            # Update input placeholder - wait for join confirmation
            self.input_bar.placeholder = "Joining channels..."
            
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
        if channel == self.current_channel:
            self.call_from_thread(self._update_member_list_ui, members)
    
    def _on_channel_joined(self, channel: str, success: bool):
        """Handle channel join completion."""
        self.call_from_thread(self._handle_channel_joined, channel, success)
    
    def _handle_channel_joined(self, channel: str, success: bool):
        """Handle channel join completion - called from main thread."""
        if success:
            # Remove from joining set and add to joined set
            self.channels_joining.discard(channel)
            self.channels_joined.add(channel)
            
            self.chat_pane.add_message("System", f"✓ Joined {channel}", is_system=True)
            
            # Update sidebar to show channel is ready
            sidebar = self.query_one("#sidebar", Sidebar)
            sidebar.mark_channel_ready(channel)
            
            # If this is the current channel, update placeholder
            if channel == self.current_channel:
                self.input_bar.placeholder = f"Message {self.current_channel}"
            
            # If all channels are joined, show ready message
            if not self.channels_joining:
                self.chat_pane.add_message("System", "✓ All channels ready! Start chatting.", is_system=True)
        else:
            # Join failed
            self.channels_joining.discard(channel)
            self.chat_pane.add_message("System", f"❌ Failed to join {channel}", is_system=True)
    
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
    
    def _update_member_list_ui(self, members: list[str]):
        """Update member list UI - called from main thread."""
        if self.member_list:
            self.member_list.update_members(members)
    
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
        elif self.current_channel in self.channels_joining:
            self.input_bar.placeholder = f"Joining {self.current_channel}..."
        elif self.current_channel not in self.channels_joined:
            self.input_bar.placeholder = f"Not joined to {self.current_channel}"
        else:
            self.input_bar.placeholder = f"Message {self.current_channel}"
        
        # Switch chat pane to show this channel's messages
        self.chat_pane.switch_channel(self.current_channel)
        
        # Show appropriate message based on channel state
        if self.current_channel in self.channels_joining:
            self.chat_pane.add_message("System", f"Joining {self.current_channel}...", is_system=True)
        elif self.current_channel not in self.channels_joined:
            self.chat_pane.add_message("System", f"Not joined to {self.current_channel}. Use /join to join.", is_system=True)
        else:
            self.chat_pane.add_message("System", f"Switched to {self.current_channel}", is_system=True)
        
        # Update member list for new channel
        if self.current_channel in self.channels_joined:
            members = self.irc.get_channel_members(self.current_channel)
            if members:
                self.member_list.update_members(members)
            else:
                # Show loading if no members yet
                self.member_list.show_loading(self.current_channel)
        else:
            # Not joined yet
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
        
        # Check if we're still joining this channel
        if self.current_channel in self.channels_joining:
            self.chat_pane.add_message("System", f"Still joining {self.current_channel}. Please wait...", is_system=True)
            return
        
        # Check if we've joined this channel
        if self.current_channel not in self.channels_joined:
            self.chat_pane.add_message("System", f"Not joined to {self.current_channel}. Use /join to join.", is_system=True)
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
            # Check if this is a private query
            is_private = args.lower().startswith("private ")
            if is_private:
                # Remove "private" prefix
                query = args[8:].strip()
            else:
                query = args.strip()
            
            # Show processing message
            self.chat_pane.add_message("System", f"🤖 Processing: {query[:50]}...", is_system=True)
            
            # Execute MCP command
            result = await self.mcp.execute(query)
            
            # Format the response
            if "error" in result:
                response_text = f"❌ Error: {result['error']}"
            elif "message" in result:
                response_text = result["message"]
            else:
                # Format result as JSON
                import json
                response_text = json.dumps(result, indent=2)
            
            # Determine where to send the response
            if is_private:
                # Private mode: Show only to user (in chat pane)
                self.chat_pane.add_embed("AI Assistant (Private)", response_text, "info")
            else:
                # Public mode: Send to IRC channel
                if self.irc_connected and self.current_channel in self.channels_joined:
                    # Send each line to IRC channel
                    lines = response_text.split('\n')
                    for line in lines:
                        if line.strip():  # Skip empty lines
                            try:
                                self.irc.send_message(self.current_channel, line)
                                # Also show in local chat pane
                                self.chat_pane.add_message("You (AI)", line, False, self.current_channel)
                            except Exception as e:
                                self.chat_pane.add_message("System", f"Failed to send to IRC: {e}", is_system=True)
                                break
                else:
                    # Not connected to IRC, show locally only
                    self.chat_pane.add_embed("AI Assistant (Local)", response_text, "info")
                    self.chat_pane.add_message("System", "💡 Not connected to IRC. Result shown locally only.", is_system=True)
        
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
                self.channels_joining.add(channel)
                self.irc.join_channel(channel)
                
                # Switch to the new channel
                self.current_channel = channel
                self.chat_pane.switch_channel(self.current_channel)
                self.chat_pane.add_message("System", f"Joining {channel}...", is_system=True)
                
                # Update UI
                self.input_bar.placeholder = f"Joining {self.current_channel}..."
                self.member_list.show_loading(channel)
        
        elif cmd == "bookmark":
            # Bookmark current or specified channel
            channel = args.strip() if args else self.current_channel
            if not channel.startswith('#'):
                channel = '#' + channel
            
            if channel in self.bookmarks:
                self.chat_pane.add_message("System", f"{channel} is already bookmarked", is_system=True)
            else:
                self.bookmarks.append(channel)
                sidebar = self.query_one("#sidebar", Sidebar)
                sidebar.add_bookmark(channel)
                self._save_bookmarks()
                self.chat_pane.add_message("System", f"⭐ Bookmarked {channel}", is_system=True)
        
        elif cmd == "unbookmark":
            # Remove bookmark from current or specified channel
            channel = args.strip() if args else self.current_channel
            if not channel.startswith('#'):
                channel = '#' + channel
            
            if channel not in self.bookmarks:
                self.chat_pane.add_message("System", f"{channel} is not bookmarked", is_system=True)
            else:
                self.bookmarks.remove(channel)
                sidebar = self.query_one("#sidebar", Sidebar)
                sidebar.remove_bookmark(channel)
                self._save_bookmarks()
                self.chat_pane.add_message("System", f"Removed bookmark from {channel}", is_system=True)
        
        elif cmd == "bookmarks":
            # List all bookmarks
            if not self.bookmarks:
                self.chat_pane.add_message("System", "No bookmarked channels", is_system=True)
            else:
                self.chat_pane.add_message("System", f"Bookmarked channels ({len(self.bookmarks)}):", is_system=True)
                for channel in self.bookmarks:
                    self.chat_pane.add_message("System", f"  ⭐ {channel}", is_system=True)
        
        else:
            self.chat_pane.add_message("System", f"Unknown command: /{cmd}", is_system=True)
            self.chat_pane.add_message("System", "Available commands: /join, /bookmark, /unbookmark, /bookmarks, /send, /grab, /ai", is_system=True)
    
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
    
    def action_toggle_bookmark(self):
        """Toggle bookmark for current channel."""
        if not self.current_channel or not self.current_channel.startswith('#'):
            if self.chat_pane:
                self.chat_pane.add_message("System", "Not in a channel. Select a channel first.", is_system=True)
            return
        
        sidebar = self.query_one("#sidebar", Sidebar)
        
        # Toggle bookmark
        is_bookmarked = sidebar.toggle_bookmark(self.current_channel)
        
        # Update app's bookmark list
        if is_bookmarked:
            if self.current_channel not in self.bookmarks:
                self.bookmarks.append(self.current_channel)
            self._save_bookmarks()
            if self.chat_pane:
                self.chat_pane.add_message("System", f"⭐ Bookmarked {self.current_channel}", is_system=True)
        else:
            if self.current_channel in self.bookmarks:
                self.bookmarks.remove(self.current_channel)
            self._save_bookmarks()
            if self.chat_pane:
                self.chat_pane.add_message("System", f"Removed bookmark from {self.current_channel}", is_system=True)
    
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
        self.channels_joining.add(channel)
        self.irc.join_channel(channel)
        
        # Update recent channels in search screen for next time
        if hasattr(self, '_channel_search_screen'):
            self._channel_search_screen.add_recent_channel(channel)
        
        # Switch to the new channel
        self.current_channel = channel
        self.chat_pane.switch_channel(self.current_channel)
        self.chat_pane.add_message("System", f"Joining {channel}...", is_system=True)
        
        # Update UI
        self.input_bar.placeholder = f"Joining {self.current_channel}..."
        self.member_list.show_loading(channel)
    
    async def on_unmount(self):
        """Clean up on exit."""
        self._save_bookmarks()
        if self.irc:
            await self.irc.disconnect()
