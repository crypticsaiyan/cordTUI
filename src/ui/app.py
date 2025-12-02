"""Main Textual application."""

import asyncio
import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Input
from textual.binding import Binding

from src.ui.widgets.chat_pane import ChatPane
from src.ui.widgets.sidebar import Sidebar, MemberList
from src.ui.screens import TeletextScreen
from src.core.irc_client import IRCClient
from src.core.mcp_client import MCPClient
from src.core.wormhole import WormholeClient
from src.core.audio import AudioEngine


class CordTUI(App):
    """The main Cord-TUI application."""
    
    CSS_PATH = "styles.tcss"
    TITLE = "Cord-TUI"
    
    BINDINGS = [
        Binding("f1", "toggle_teletext", "Teletext", show=True),
        Binding("ctrl+c", "quit", "Quit", show=True),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = self._load_config()
        self.current_channel = "#general"
        self.irc_connected = False
        
        # Initialize backend components
        server = self.config["servers"][0]
        self.irc = IRCClient(
            host=server["host"],
            port=server["port"],
            nick=server["nick"],
            ssl=server["ssl"]
        )
        self.mcp = MCPClient()
        self.wormhole = WormholeClient()
        self.audio = AudioEngine(
            enabled=self.config["audio"]["enabled"],
            volume=self.config["audio"]["volume"]
        )
        
        # Set up callbacks
        self.irc.set_message_callback(self._on_irc_message)
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
        """Initialize connections on mount."""
        self.chat_pane = self.query_one("#chat-pane", ChatPane)
        self.input_bar = self.query_one("#input-bar", Input)
        
        # Welcome message
        self.chat_pane.add_message("System", "Welcome to Cord-TUI! 🚀", is_system=True)
        self.chat_pane.add_message("System", "Press F1 for Teletext Dashboard", is_system=True)
        
        # Connect to IRC in background
        asyncio.create_task(self._connect_irc())
    
    async def _connect_irc(self):
        """Connect to IRC server."""
        try:
            self.chat_pane.add_message("System", f"Connecting to {self.irc.host}:{self.irc.port}...", is_system=True)
            await self.irc.connect()
            
            # Give it a moment to connect
            await asyncio.sleep(2)
            
            # Join channels
            for channel in self.config["servers"][0]["channels"]:
                self.irc.join_channel(channel)
                self.chat_pane.add_message("System", f"Joining {channel}...", is_system=True)
            
            self.chat_pane.add_message("System", "✓ Connected to IRC! You can now chat.", is_system=True)
            self.irc_connected = True
        except Exception as e:
            self.chat_pane.add_message("System", f"✗ IRC connection failed: {e}", is_system=True)
            self.chat_pane.add_message("System", "Running in local mode. Messages won't reach others.", is_system=True)
            self.irc_connected = False
    
    def _on_irc_message(self, nick: str, target: str, message: str):
        """Handle incoming IRC messages."""
        self.call_from_thread(self.chat_pane.add_message, nick, message)
        self.audio.process_log(message)
    
    def _on_wormhole_status(self, status: str):
        """Handle wormhole status updates."""
        self.call_from_thread(self.chat_pane.add_message, "Wormhole", status, is_system=True)
    
    def on_sidebar_channel_selected(self, event: Sidebar.ChannelSelected):
        """Handle channel selection from sidebar."""
        self.current_channel = event.channel
        self.input_bar.placeholder = f"Message {self.current_channel}"
        self.chat_pane.add_message("System", f"Switched to {self.current_channel}", is_system=True)
    
    async def on_input_submitted(self, event: Input.Submitted):
        """Handle message submission."""
        message = event.value.strip()
        if not message:
            return
        
        self.input_bar.value = ""
        
        # Handle commands
        if message.startswith("/"):
            await self._handle_command(message)
        else:
            # Send to IRC
            if self.irc_connected:
                try:
                    self.irc.send_message(self.current_channel, message)
                    self.chat_pane.add_message("You", message)
                except Exception as e:
                    self.chat_pane.add_message("System", f"Failed to send: {e}", is_system=True)
            else:
                self.chat_pane.add_message("You", message)
                self.chat_pane.add_message("System", "(Local only - not connected to IRC)", is_system=True)
    
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
            else:
                # Format result as JSON
                import json
                result_str = json.dumps(result, indent=2)
                self.chat_pane.add_embed("AI Result", f"```json\n{result_str}\n```", "success")
        
        else:
            self.chat_pane.add_message("System", f"Unknown command: /{cmd}", is_system=True)
    
    def action_toggle_teletext(self):
        """Toggle the Teletext dashboard."""
        self.push_screen(TeletextScreen(app_ref=self))
    
    async def on_unmount(self):
        """Clean up on exit."""
        await self.irc.disconnect()
