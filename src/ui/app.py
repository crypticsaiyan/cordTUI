"""Main Textual application."""

import asyncio
import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Input, Tree
from textual.binding import Binding
from textual.message import Message
from textual.command import Provider, Hit, Hits

from src.ui.widgets.chat_pane import ChatPane
from src.ui.widgets.sidebar import Sidebar, MemberList
from src.ui.widgets.channel_search import ChannelSearchScreen
from src.ui.widgets.command_palette import SlashCommandPalette
from src.ui.screens import TeletextScreen, HomeScreen, KeysScreen, VolumeScreen
from src.core.irc_client import IRCClient
from src.core.mcp_client import MCPClient
from src.core.wormhole import WormholeClient
from src.core.audio import AudioEngine


class DMNotification(Message):
    """Message to notify of incoming DM."""
    def __init__(self, from_nick: str, content: str):
        super().__init__()
        self.from_nick = from_nick
        self.content = content


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


class PhosphorCommands(Provider):
    """Custom command provider for phosphor app."""

    @property
    def commands(self):
        """Return all available commands."""
        return [
            ("Show Keyboard Shortcuts", "View all keyboard shortcuts and commands", self._show_keys),
            ("Adjust Volume", "Change audio volume and mute settings", self._show_volume),
            ("Toggle Teletext Dashboard", "Open the retro teletext dashboard", self._toggle_teletext),
            ("Search Channels", "Search and join IRC channels", self._search_channels),
            ("Toggle Bookmark", "Bookmark or unbookmark current channel", self._toggle_bookmark),
            ("Theme: Default", "Switch to default Discord-inspired theme", self._theme_default),
            ("Theme: Halloween 🎃", "Switch to spooky Halloween theme", self._theme_halloween),
        ]

    async def search(self, query: str) -> Hits:
        """Search for commands matching the query."""
        matcher = self.matcher(query)
        
        for name, help_text, callback in self.commands:
            score = matcher.match(name)
            if score > 0:
                yield Hit(score, name, callback, help=help_text)

    async def discover(self) -> Hits:
        """Show all commands when palette first opens (no query)."""
        for name, help_text, callback in self.commands:
            yield Hit(1.0, name, callback, help=help_text)

    async def _show_keys(self) -> None:
        """Show the keyboard shortcuts screen."""
        self.app.push_screen(KeysScreen())

    async def _show_volume(self) -> None:
        """Show the volume control screen."""
        self.app.push_screen(VolumeScreen())

    async def _toggle_teletext(self) -> None:
        """Toggle the teletext dashboard."""
        if hasattr(self.app, 'action_toggle_teletext'):
            self.app.action_toggle_teletext()

    async def _search_channels(self) -> None:
        """Open channel search."""
        if hasattr(self.app, 'action_search_channels'):
            self.app.action_search_channels()

    async def _toggle_bookmark(self) -> None:
        """Toggle bookmark on current channel."""
        if hasattr(self.app, 'action_toggle_bookmark'):
            self.app.action_toggle_bookmark()

    async def _theme_default(self) -> None:
        """Switch to default theme."""
        if hasattr(self.app, 'set_theme'):
            self.app.set_theme("default")

    async def _theme_halloween(self) -> None:
        """Switch to Halloween theme."""
        if hasattr(self.app, 'set_theme'):
            self.app.set_theme("halloween")


class Phosphor(App):
    """The main phosphor application."""
    
    CSS_PATH = "styles.tcss"
    TITLE = "phosphor"
    
    COMMANDS = {PhosphorCommands}
    
    BINDINGS = [
        Binding("f1", "toggle_teletext", "Teletext", show=True),
        Binding("ctrl+j", "search_channels", "Join", show=True),
        Binding("ctrl+b", "toggle_bookmark", "Bookmark", show=True),
        Binding("question_mark", "show_keys", "Keys", show=True),
        Binding("left", "focus_prev_section", "Left", show=False),
        Binding("right", "focus_next_section", "Right", show=False),
        Binding("slash", "focus_input", "Focus", show=False),
        Binding("ctrl+slash", "blur_input", "Blur", show=False),
        Binding("ctrl+c", "quit", "Quit", show=True),
    ]
    
    # Available themes
    THEMES = ["default", "halloween"]
    
    # Track which section is focused: 0=sidebar, 1=chat, 2=members
    focused_section = 0
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = self._load_config()
        self.bookmarks = self._load_bookmarks()
        self.current_channel = "#general"
        self.current_dm = None  # Currently active DM conversation (nick)
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
        self.active_theme = self._load_theme()  # Load saved theme
        
        # Set up wormhole callback
        self.wormhole.set_status_callback(self._on_wormhole_status)
    
    def _load_config(self) -> dict:
        """Load configuration from .phosphor/config.json."""
        config_path = Path(".phosphor/config.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}
    
    def _load_bookmarks(self) -> list[str]:
        """Load bookmarked channels from .phosphor/bookmarks.json."""
        bookmarks_path = Path(".phosphor/bookmarks.json")
        if bookmarks_path.exists():
            try:
                with open(bookmarks_path) as f:
                    data = json.load(f)
                    return data.get("channels", [])
            except Exception:
                return []
        return []
    
    def _save_bookmarks(self):
        """Save bookmarked channels to .phosphor/bookmarks.json."""
        bookmarks_path = Path(".phosphor/bookmarks.json")
        bookmarks_path.parent.mkdir(exist_ok=True)
        try:
            with open(bookmarks_path, 'w') as f:
                json.dump({"channels": self.bookmarks}, f, indent=2)
        except Exception as e:
            if self.chat_pane:
                self.chat_pane.add_message("System", f"Failed to save bookmarks: {e}", is_system=True)
    
    def _load_theme(self) -> str:
        """Load saved theme from config."""
        theme_path = Path(".phosphor/theme.json")
        if theme_path.exists():
            try:
                with open(theme_path) as f:
                    data = json.load(f)
                    return data.get("theme", "default")
            except Exception:
                pass
        return "default"
    
    def _save_theme(self, theme: str):
        """Save theme preference."""
        theme_path = Path(".phosphor/theme.json")
        theme_path.parent.mkdir(exist_ok=True)
        try:
            with open(theme_path, 'w') as f:
                json.dump({"theme": theme}, f, indent=2)
        except Exception:
            pass
    
    def set_theme(self, theme: str):
        """Set the application theme."""
        if theme not in self.THEMES:
            theme = "default"
        
        self.active_theme = theme
        self._save_theme(theme)
        self._apply_theme()
        
        if self.chat_pane:
            if theme == "halloween":
                self.chat_pane.add_message("System", "🎃 Halloween theme activated! Spooky!", is_system=True)
            else:
                self.chat_pane.add_message("System", "Theme switched to default", is_system=True)
    
    def _apply_theme(self):
        """Apply the current theme to all screens."""
        # Remove all theme classes first
        for theme_class in self.THEMES:
            if theme_class != "default":
                self.remove_class(theme_class)
        
        # Apply new theme class (default has no class)
        if self.active_theme != "default":
            self.add_class(self.active_theme)
    
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
                yield SlashCommandPalette(id="command-palette")
                yield Input(
                    placeholder=f"Message {self.current_channel}",
                    id="input-bar"
                )
            
            # Right sidebar - members
            yield MemberList(id="member-list")
        
        yield Footer()
    
    async def on_mount(self):
        """Show home screen first."""
        # Apply saved theme
        self._apply_theme()
        self.push_screen(HomeScreen(config=self.config, theme=self.active_theme))

    def on_home_screen_settings_confirmed(self, event: HomeScreen.SettingsConfirmed):
        """Handle settings from home screen."""
        import random
        
        # Use the selected server from the event
        server = event.server
        
        # Update config with user settings
        self.config["audio"]["enabled"] = event.audio_enabled
        self.config["audio"]["volume"] = event.volume
        
        # Store selected server config for later use
        self.selected_server = server
        
        # Use the nick as-is - IRC client will handle conflicts automatically
        # by appending a random suffix if the nick is already taken (433 error)
        nick = event.nick.strip()
        # Truncate if too long (IRC max is usually 30)
        if len(nick) > 30:
            nick = nick[:30]
        
        # Initialize IRC client with chosen server and nick
        self.irc = IRCClient(
            host=server["host"],
            port=server["port"],
            nick=nick,
            ssl=server.get("ssl", False)
        )
        self.irc.set_message_callback(self._on_irc_message)
        self.irc.set_members_callback(self._on_members_update)
        self.irc.set_channel_list_callback(self._on_channel_list_received)
        self.irc.set_join_callback(self._on_channel_joined)
        self.irc.set_nick_callback(self._on_nick_update)
        
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
        
        # Set current nick for "you" highlighting
        self.chat_pane.current_nick = self.irc.nick
        self.member_list.set_current_nick(self.irc.nick)
        
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
        self.chat_pane.add_message("System", f"Welcome to phosphor! 🚀", is_system=True)
        self.chat_pane.add_message("System", f"Connecting to {server_name} as {self.irc.nick}...", is_system=True)
        self.chat_pane.add_message("System", "Press F1 for Teletext Dashboard", is_system=True)
        
        # Connect to IRC in background
        asyncio.create_task(self._connect_irc())
    
    async def _connect_irc(self):
        """Connect to IRC server."""
        try:
            self.connection_status = "connecting"
            self.chat_pane.add_message("System", f"Connecting to {self.irc.host}:{self.irc.port}...", is_system=True)
            
            # Quick connectivity check with shorter timeout
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)  # Reduced from 5 to 3 seconds
                sock.connect((self.irc.host, self.irc.port))
                sock.close()
            except (socket.error, OSError, socket.timeout) as e:
                self.chat_pane.add_message("System", f"❌ Cannot reach {self.irc.host}:{self.irc.port}", is_system=True)
                self.chat_pane.add_message("System", "Check your internet connection.", is_system=True)
                self.connection_status = "offline"
                self.input_bar.placeholder = "Offline - Check connection"
                return
            
            await self.irc.connect()
            
            # Wait for connection with timeout - poll for client readiness
            max_wait = 10  # Maximum 10 seconds to connect
            waited = 0
            while waited < max_wait:
                if self.irc.client is not None:
                    break
                await asyncio.sleep(0.3)
                waited += 0.3
            
            if self.irc.client is None:
                self.chat_pane.add_message("System", "❌ Connection timed out", is_system=True)
                self.connection_status = "failed"
                self.input_bar.placeholder = "Connection failed - restart app"
                return
            
            self.chat_pane.add_message("System", "✓ Connected! Confirming nickname...", is_system=True)
            
            # Wait for nickname confirmation before joining channels
            # The server will send 001 (RPL_WELCOME) when nick is confirmed
            # or 433 (ERR_NICKNAMEINUSE) if taken, which triggers auto-retry
            max_nick_wait = 15  # Maximum 15 seconds for nick negotiation
            nick_waited = 0
            while nick_waited < max_nick_wait:
                if self.irc.is_nick_confirmed():
                    break
                await asyncio.sleep(0.3)
                nick_waited += 0.3
            
            if not self.irc.is_nick_confirmed():
                self.chat_pane.add_message("System", "❌ Nickname negotiation timed out", is_system=True)
                self.connection_status = "failed"
                self.input_bar.placeholder = "Connection failed - restart app"
                return
            
            self.connection_status = "connected"
            self.irc_connected = True
            
            # Update UI with confirmed nick (may have changed due to conflict)
            confirmed_nick = self.irc.get_confirmed_nick()
            self.chat_pane.current_nick = confirmed_nick
            if self.member_list:
                self.member_list.set_current_nick(confirmed_nick)
            
            self.chat_pane.add_message("System", f"✓ Ready as {confirmed_nick}!", is_system=True)
            
            # Now join all channels with confirmed nickname
            server_channels = self.selected_server.get("channels", [])
            for channel in server_channels:
                self.channels_joining.add(channel)
                self.irc.join_channel(channel)
            
            if server_channels:
                self.chat_pane.add_message("System", f"Joining {len(server_channels)} channel(s)...", is_system=True)
            
            # Wait briefly for initial joins, but don't block - callbacks will handle completion
            await asyncio.sleep(0.5)
            
            # Update input placeholder
            if self.current_channel in self.channels_joined:
                self.input_bar.placeholder = f"Message {self.current_channel}"
            else:
                self.input_bar.placeholder = f"Joining {self.current_channel}..."
            
        except Exception as e:
            self.chat_pane.add_message("System", f"IRC connection failed: {e}", is_system=True)
            self.chat_pane.add_message("System", "Check your internet connection and try restarting.", is_system=True)
            self.connection_status = "failed"
            self.irc_connected = False
    
    def _on_irc_message(self, nick: str, target: str, message: str):
        """Handle incoming IRC messages."""
        # miniirc runs in a separate thread, so we need call_from_thread
        
        # Check if this is a private message (target is our nick, not a channel)
        if target == self.irc.get_confirmed_nick():
            # This is a DM from 'nick' to us
            self.call_from_thread(self._handle_dm_received, nick, message)
        else:
            # Regular channel message
            self.call_from_thread(self._handle_channel_message, nick, target, message)
        
        self.audio.process_log(message)
    
    def _handle_channel_message(self, nick: str, channel: str, message: str):
        """Handle received channel message - called from main thread."""
        # Add message to chat pane
        self.chat_pane.add_message(nick, message, False, channel)
        
        # Play retro notification sound for new messages (not from self)
        if self.audio and nick != self.irc.get_confirmed_nick():
            self.audio.play_notification()
        
        # If not currently viewing this channel, increment unread count
        if channel != self.current_channel:
            sidebar = self.query_one("#sidebar", Sidebar)
            sidebar.increment_channel_unread(channel)
    
    def _handle_dm_received(self, from_nick: str, message: str):
        """Handle received DM - called from main thread."""
        sidebar = self.query_one("#sidebar", Sidebar)
        
        # Add to DM messages
        self.chat_pane.add_message(from_nick, message, False, dm_nick=from_nick)
        
        # Play distinct retro DM notification sound
        if self.audio:
            self.audio.play_dm_notification()
        
        # If not currently viewing this DM, show notification and increment unread
        if self.current_dm != from_nick:
            sidebar.increment_dm_unread(from_nick)
            # Show notification in current view
            self.chat_pane.add_message("System", f"💬 New DM from {from_nick}", is_system=True)
        else:
            # Ensure conversation is in sidebar
            sidebar.add_dm_conversation(from_nick)
    
    def _on_members_update(self, channel: str, members: list[str]):
        """Handle member list updates."""
        if channel == self.current_channel:
            self.call_from_thread(self._update_member_list_ui, members)
    
    def _on_nick_update(self, nick: str, success: bool, message: str):
        """Handle nickname confirmation/change from IRC server."""
        self.call_from_thread(self._handle_nick_update, nick, success, message)
    
    def _handle_nick_update(self, nick: str, success: bool, message: str):
        """Handle nickname update - called from main thread."""
        if success and nick:
            original_nick = self.irc.original_nick
            
            # Update UI with confirmed nick
            if self.chat_pane:
                self.chat_pane.current_nick = nick
                # Only show "nickname taken" message if it actually changed from original
                if nick != original_nick:
                    self.chat_pane.add_message("System", f"⚠️ Nickname '{original_nick}' was taken. Using '{nick}' instead.", is_system=True)
            
            if self.member_list:
                self.member_list.set_current_nick(nick)
        elif not success:
            if self.chat_pane:
                self.chat_pane.add_message("System", f"❌ Nickname error: {message}", is_system=True)
    
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
        # Wormhole runs as async subprocess in same thread, so call directly
        if self.chat_pane:
            self.chat_pane.add_message("Wormhole", status, is_system=True)
    
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
        self.current_dm = None  # Clear DM mode
        
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
    
    def on_sidebar_direct_message_selected(self, event: Sidebar.DirectMessageSelected):
        """Handle DM selection from sidebar."""
        self.current_dm = event.nick
        self.current_channel = None  # Clear channel mode
        
        # Update placeholder
        self.input_bar.placeholder = f"Message @{event.nick}"
        
        # Switch chat pane to show this DM conversation
        self.chat_pane.switch_dm(event.nick)
        
        # Clear unread count
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.clear_dm_unread(event.nick)
        
        # Show DM header
        self.chat_pane.add_message("System", f"💬 Direct message with {event.nick}", is_system=True)
        
        # Hide member list for DMs (or show just the DM partner)
        self.member_list.update_members([event.nick])
    
    def on_member_list_member_clicked(self, event: MemberList.MemberClicked):
        """Handle member click to start DM."""
        nick = event.nick
        
        if not self.irc_connected:
            self.chat_pane.add_message("System", "Not connected to IRC.", is_system=True)
            return
        
        # Start DM with this user
        self._start_dm(nick)
    
    def _start_dm(self, nick: str):
        """Start or switch to a DM conversation with a user."""
        sidebar = self.query_one("#sidebar", Sidebar)
        
        # Add to DM conversations if not already there
        sidebar.add_dm_conversation(nick)
        
        # Switch to DM view
        self.current_dm = nick
        self.current_channel = None
        
        # Update UI
        self.input_bar.placeholder = f"Message @{nick}"
        self.chat_pane.switch_dm(nick)
        sidebar.select_dm(nick)
        
        # Show DM header
        self.chat_pane.add_message("System", f"💬 Direct message with {nick}", is_system=True)
        self.chat_pane.add_message("System", "Type a message to start chatting.", is_system=True)

    def on_input_changed(self, event: Input.Changed):
        """Handle input text changes to show command palette."""
        if not hasattr(self, "input_bar") or self.input_bar is None:
            return

        try:
            palette = self.query_one("#command-palette", SlashCommandPalette)
        except Exception:
            return

        text = event.value

        # Show palette when typing starts with /
        if text.startswith("/") and " " not in text:
            palette.show()
            palette.filter(text)
        else:
            palette.hide()

    def on_key(self, event) -> None:
        """Handle key events for command palette navigation."""
        if not hasattr(self, "input_bar") or self.input_bar is None:
            return

        # Only handle when input is focused
        if not self.input_bar.has_focus:
            return

        try:
            palette = self.query_one("#command-palette", SlashCommandPalette)
        except Exception:
            return

        if not palette.is_visible():
            return

        # Handle navigation keys
        if event.key == "up":
            palette.move_up()
            event.prevent_default()
            event.stop()
        elif event.key == "down":
            palette.move_down()
            event.prevent_default()
            event.stop()
        elif event.key == "tab" or event.key == "enter":
            # Auto-complete the selected command
            cmd = palette.select_current()
            if cmd:
                self.input_bar.value = cmd + " "
                self.input_bar.cursor_position = len(self.input_bar.value)
                palette.hide()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            palette.hide()
            event.prevent_default()
            event.stop()

    async def on_input_submitted(self, event: Input.Submitted):
        """Handle message submission."""
        # Ignore if input_bar not yet initialized (e.g., from HomeScreen)
        if not hasattr(self, "input_bar") or self.input_bar is None:
            return

        # Hide command palette on submit
        try:
            palette = self.query_one("#command-palette", SlashCommandPalette)
            palette.hide()
        except Exception:
            pass

        message = event.value.strip()
        if not message:
            return

        self.input_bar.value = ""
        
        # Check if we're connected
        if not self.irc_connected:
            self.chat_pane.add_message("System", "Not connected to IRC. Please wait for connection.", is_system=True)
            return
        
        # Handle commands
        if message.startswith("/"):
            await self._handle_command(message)
            return
        
        # Check if we're in DM mode
        if self.current_dm:
            # Send DM
            try:
                self.irc.send_message(self.current_dm, message)
                # Add to DM history
                self.chat_pane.add_message(self.irc.get_confirmed_nick(), message, False, dm_nick=self.current_dm)
            except Exception as e:
                self.chat_pane.add_message("System", f"Failed to send DM: {e}", is_system=True)
            return
        
        # Check if we're in a valid channel
        if not self.current_channel or not self.current_channel.startswith("#"):
            self.chat_pane.add_message("System", "Not in a channel or DM. Select one first.", is_system=True)
            return
        
        # Check if we're still joining this channel
        if self.current_channel in self.channels_joining:
            self.chat_pane.add_message("System", f"Still joining {self.current_channel}. Please wait...", is_system=True)
            return
        
        # Check if we've joined this channel
        if self.current_channel not in self.channels_joined:
            self.chat_pane.add_message("System", f"Not joined to {self.current_channel}. Use /join to join.", is_system=True)
            return
        
        # Send to channel
        try:
            self.irc.send_message(self.current_channel, message)
            # Add to current channel's history using actual nick for consistent coloring
            self.chat_pane.add_message(self.irc.get_confirmed_nick(), message, False, self.current_channel)
        except Exception as e:
            self.chat_pane.add_message("System", f"Failed to send: {e}", is_system=True)
    
    async def _handle_command(self, command: str):
        """Handle slash commands."""
        parts = command[1:].split(maxsplit=1)
        if not parts or not parts[0]:
            # Just "/" with no command
            self.chat_pane.add_message(
                "System",
                "Available commands: /join, /msg, /dm, /close, /bookmark, /unbookmark, /bookmarks, /send, /grab, /ai",
                is_system=True,
            )
            return
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == "send":
            # Send file via wormhole - works best in DM context
            if not args:
                self.chat_pane.add_message("System", "Usage: /send <filepath>", is_system=True)
                self.chat_pane.add_message("System", "Tip: Use in a DM to automatically share the code with the recipient.", is_system=True)
                return
            
            filepath = args.strip()
            
            # Check if file exists
            from pathlib import Path
            if not Path(filepath).exists():
                self.chat_pane.add_message("System", f"❌ File not found: {filepath}", is_system=True)
                return
            
            self.chat_pane.add_message("System", f"📤 Preparing to send: {filepath}...", is_system=True)
            code = await self.wormhole.send_file(filepath)
            
            if code.startswith("error") or code == "wormhole-not-found":
                self.chat_pane.add_message("System", f"❌ Failed to initiate transfer: {code}", is_system=True)
                self.chat_pane.add_message("System", "Make sure 'magic-wormhole' is installed: pip install magic-wormhole", is_system=True)
                return
            
            # If we're in a DM, automatically send the code to the recipient
            if self.current_dm:
                try:
                    # Send the wormhole code to the DM recipient
                    transfer_msg = f"📁 File transfer: {Path(filepath).name} | Use: /grab {code}"
                    self.irc.send_message(self.current_dm, transfer_msg)
                    self.chat_pane.add_message(self.irc.get_confirmed_nick(), transfer_msg, False, dm_nick=self.current_dm)
                    self.chat_pane.add_embed(
                        "File Transfer Started",
                        f"File: {Path(filepath).name}\nCode: `{code}`\n\n✓ Code sent to {self.current_dm}",
                        "success"
                    )
                except Exception as e:
                    self.chat_pane.add_message("System", f"Failed to send code to {self.current_dm}: {e}", is_system=True)
                    self.chat_pane.add_embed(
                        "File Transfer Ready",
                        f"Code: `{code}`\n\nManually share: /grab {code}",
                        "warning"
                    )
            else:
                # Not in DM - just show the code
                self.chat_pane.add_embed(
                    "File Transfer Ready",
                    f"Code: `{code}`\n\nRecipient should run: `/grab {code}`\n\n💡 Tip: Use /send in a DM to auto-share the code.",
                    "success"
                )
        
        elif cmd == "grab":
            # Receive file via wormhole
            if not args:
                self.chat_pane.add_message("System", "Usage: /grab <code>", is_system=True)
                self.chat_pane.add_message("System", "Example: /grab 7-guitar-ocean", is_system=True)
                return
            
            code = args.strip()
            self.chat_pane.add_message("System", f"📥 Receiving file with code: {code}...", is_system=True)
            
            # Determine download directory
            from pathlib import Path
            download_dir = Path.home() / "Downloads"
            if not download_dir.exists():
                download_dir = Path(".")
            
            success = await self.wormhole.receive_file(code, str(download_dir))
            
            if success:
                self.chat_pane.add_embed(
                    "File Received",
                    f"✓ Transfer complete!\nSaved to: {download_dir}",
                    "success"
                )
                # Notify sender if in DM
                if self.current_dm:
                    try:
                        self.irc.send_message(self.current_dm, "✓ File received successfully!")
                        self.chat_pane.add_message(self.irc.get_confirmed_nick(), "✓ File received successfully!", False, dm_nick=self.current_dm)
                    except Exception:
                        pass
            else:
                self.chat_pane.add_embed(
                    "Transfer Failed",
                    "❌ Could not receive file. Check the code and try again.\nMake sure 'magic-wormhole' is installed.",
                    "error"
                )
        
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
                                # Also show in local chat pane using actual nick
                                self.chat_pane.add_message(self.irc.get_confirmed_nick(), line, False, self.current_channel)
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
                
                # Join the channel
                self.channels_joining.add(channel)
                self.irc.join_channel(channel)
                
                # Switch to the new channel
                self.current_channel = channel
                self.chat_pane.switch_channel(self.current_channel)
                self.chat_pane.add_message("System", f"Joined [cyan]{channel}[/]", is_system=True)
                
                # Update UI and focus the channel in sidebar
                self.input_bar.placeholder = f"Message {self.current_channel}"
                self.member_list.show_loading(channel)
                sidebar._refresh_tree(select_channel=channel)
        
        elif cmd == "bookmark":
            # Bookmark current or specified channel
            channel = args.strip() if args else self.current_channel
            if not channel.startswith("#"):
                channel = "#" + channel

            sidebar = self.query_one("#sidebar", Sidebar)
            if sidebar.is_bookmarked(channel):
                self.chat_pane.add_message(
                    "System", f"{channel} is already bookmarked", is_system=True
                )
            else:
                sidebar.add_bookmark(channel)
                if channel not in self.bookmarks:
                    self.bookmarks.append(channel)
                self._save_bookmarks()
                self.chat_pane.add_message(
                    "System", f"⭐ Bookmarked {channel}", is_system=True
                )

        elif cmd == "unbookmark":
            # Remove bookmark from current or specified channel
            channel = args.strip() if args else self.current_channel
            if not channel.startswith("#"):
                channel = "#" + channel

            sidebar = self.query_one("#sidebar", Sidebar)
            if not sidebar.is_bookmarked(channel):
                self.chat_pane.add_message(
                    "System", f"{channel} is not bookmarked", is_system=True
                )
            else:
                sidebar.remove_bookmark(channel)
                if channel in self.bookmarks:
                    self.bookmarks.remove(channel)
                self._save_bookmarks()
                self.chat_pane.add_message(
                    "System", f"Removed bookmark from {channel}", is_system=True
                )
        
        elif cmd == "bookmarks":
            # List all bookmarks
            if not self.bookmarks:
                self.chat_pane.add_message("System", "No bookmarked channels", is_system=True)
            else:
                self.chat_pane.add_message("System", f"Bookmarked channels ({len(self.bookmarks)}):", is_system=True)
                for channel in self.bookmarks:
                    self.chat_pane.add_message("System", f"  ⭐ {channel}", is_system=True)
        
        elif cmd == "msg" or cmd == "dm":
            # Start or send a DM
            if not args:
                self.chat_pane.add_message("System", "Usage: /msg <nick> [message]", is_system=True)
                return
            
            parts = args.split(maxsplit=1)
            target_nick = parts[0]
            dm_message = parts[1] if len(parts) > 1 else None
            
            # Add to DM conversations
            sidebar = self.query_one("#sidebar", Sidebar)
            sidebar.add_dm_conversation(target_nick)
            
            if dm_message:
                # Send the message directly
                try:
                    self.irc.send_message(target_nick, dm_message)
                    self.chat_pane.add_message(self.irc.get_confirmed_nick(), dm_message, False, dm_nick=target_nick)
                    self.chat_pane.add_message("System", f"💬 Sent DM to {target_nick}", is_system=True)
                except Exception as e:
                    self.chat_pane.add_message("System", f"Failed to send DM: {e}", is_system=True)
            else:
                # Just switch to DM view
                self._start_dm(target_nick)
        
        elif cmd == "close":
            # Close current DM conversation
            if self.current_dm:
                sidebar = self.query_one("#sidebar", Sidebar)
                closed_nick = self.current_dm
                sidebar.remove_dm_conversation(self.current_dm)
                self.current_dm = None
                
                # Switch back to first channel
                if self.channels_joined:
                    first_channel = list(self.channels_joined)[0]
                    self.current_channel = first_channel
                    self.chat_pane.switch_channel(first_channel)
                    self.input_bar.placeholder = f"Message {first_channel}"
                    self.chat_pane.add_message("System", f"Closed DM with {closed_nick}", is_system=True)
            else:
                self.chat_pane.add_message("System", "Not in a DM conversation.", is_system=True)
        
        else:
            self.chat_pane.add_message("System", f"Unknown command: /{cmd}", is_system=True)
            self.chat_pane.add_message("System", "Available commands: /join, /msg, /dm, /close, /bookmark, /unbookmark, /bookmarks, /send, /grab, /ai", is_system=True)
    
    def action_toggle_teletext(self):
        """Toggle the Teletext dashboard."""
        self.push_screen(TeletextScreen(app_ref=self))
    
    def action_show_keys(self):
        """Show the keyboard shortcuts screen."""
        self.push_screen(KeysScreen())
    
    def action_focus_prev_section(self):
        """Focus the previous section (left arrow)."""
        # Don't navigate if input has focus and has content
        if self.input_bar and self.input_bar.has_focus and self.input_bar.value:
            return
        
        self.focused_section = (self.focused_section - 1) % 3
        self._focus_current_section()
    
    def action_focus_next_section(self):
        """Focus the next section (right arrow)."""
        # Don't navigate if input has focus and has content
        if self.input_bar and self.input_bar.has_focus and self.input_bar.value:
            return
        
        self.focused_section = (self.focused_section + 1) % 3
        self._focus_current_section()
    
    def action_focus_input(self):
        """Focus the input bar (/ key)."""
        if self.input_bar:
            self.input_bar.focus()
            self.focused_section = 1  # Chat section
    
    def action_blur_input(self):
        """Blur/defocus the input bar (ctrl+/ key)."""
        if self.input_bar and self.input_bar.has_focus:
            self.input_bar.blur()
            # Focus the chat pane instead
            if self.chat_pane:
                self.chat_pane.focus()
    
    def _focus_current_section(self):
        """Focus the widget in the current section."""
        try:
            if self.focused_section == 0:
                # Focus sidebar (channel tree)
                sidebar = self.query_one("#sidebar", Sidebar)
                tree = sidebar.query_one(Tree)
                tree.focus()
            elif self.focused_section == 1:
                # Focus chat pane
                if self.chat_pane:
                    self.chat_pane.focus()
            elif self.focused_section == 2:
                # Focus member list
                if self.member_list:
                    self.member_list.focus()
        except Exception:
            pass  # Ignore if widgets not yet mounted
    
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
        sidebar = self.query_one("#sidebar", Sidebar)
        
        # Check if already joined
        if channel in self.channels_joined:
            # Just switch to the channel
            self.current_channel = channel
            self.chat_pane.switch_channel(self.current_channel)
            self.chat_pane.add_message("System", f"Switched to [cyan]{channel}[/]", is_system=True)
            self.input_bar.placeholder = f"Message {self.current_channel}"
            sidebar.select_channel(channel)
            return
        
        # Add to sidebar if not already there
        if channel not in sidebar.channels:
            sidebar.channels.append(channel)
        
        # Join the channel
        self.channels_joining.add(channel)
        self.irc.join_channel(channel)
        
        # Update recent channels in search screen for next time
        if hasattr(self, '_channel_search_screen'):
            self._channel_search_screen.add_recent_channel(channel)
        
        # Switch to the new channel
        self.current_channel = channel
        self.chat_pane.switch_channel(self.current_channel)
        self.chat_pane.add_message("System", f"Joined [cyan]{channel}[/]", is_system=True)
        
        # Update UI and focus the channel in sidebar
        self.input_bar.placeholder = f"Message {self.current_channel}"

        self.member_list.show_loading(channel)
        sidebar._refresh_tree(select_channel=channel)
    
    async def on_unmount(self):
        """Clean up on exit."""
        self._save_bookmarks()
        if self.irc:
            await self.irc.disconnect()
