"""Screen definitions for different views."""

import asyncio
import time
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Input, Button, Switch, Label
from textual.message import Message


LOGO = """
[green]██████╗ ██╗  ██╗ ██████╗ ███████╗[/][cyan]██████╗ [/][green]██╗  ██╗ ██████╗ ██████╗ [/]
[green]██╔══██╗██║  ██║██╔═══██╗██╔════╝[/][cyan]██╔══██╗[/][green]██║  ██║██╔═══██╗██╔══██╗[/]
[green]██████╔╝███████║██║   ██║███████╗[/][cyan]██████╔╝[/][green]███████║██║   ██║██████╔╝[/]
[green]██╔═══╝ ██╔══██║██║   ██║╚════██║[/][cyan]██╔═══╝ [/][green]██╔══██║██║   ██║██╔══██╗[/]
[green]██║     ██║  ██║╚██████╔╝███████║[/][cyan]██║     [/][green]██║  ██║╚██████╔╝██║  ██║[/]
[green]╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝[/][cyan]╚═╝     [/][green]╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝[/]
"""

LOGO_HALLOWEEN = """
[#ff6600]██████╗ ██╗  ██╗ ██████╗ ███████╗[/][#9966ff]██████╗ [/][#ff6600]██╗  ██╗ ██████╗ ██████╗ [/]
[#ff6600]██╔══██╗██║  ██║██╔═══██╗██╔════╝[/][#9966ff]██╔══██╗[/][#ff6600]██║  ██║██╔═══██╗██╔══██╗[/]
[#ff9900]██████╔╝███████║██║   ██║███████╗[/][#cc66ff]██████╔╝[/][#ff9900]███████║██║   ██║██████╔╝[/]
[#ff9900]██╔═══╝ ██╔══██║██║   ██║╚════██║[/][#cc66ff]██╔═══╝ [/][#ff9900]██╔══██║██║   ██║██╔══██╗[/]
[#ffcc00]██║     ██║  ██║╚██████╔╝███████║[/][#ff66ff]██║     [/][#ffcc00]██║  ██║╚██████╔╝██║  ██║[/]
[#ffcc00]╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝[/][#ff66ff]╚═╝     [/][#ffcc00]╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝[/]
"""


def _load_last_nick() -> str:
    """Load the last used nickname from settings."""
    settings_path = Path(".phosphor/last_nick.json")
    if settings_path.exists():
        try:
            with open(settings_path) as f:
                data = json.load(f)
                return data.get("nick", "phosphor_user")
        except Exception:
            pass
    return "phosphor_user"


def _save_last_nick(nick: str):
    """Save the nickname for future use."""
    settings_path = Path(".phosphor/last_nick.json")
    settings_path.parent.mkdir(exist_ok=True)
    try:
        with open(settings_path, 'w') as f:
            json.dump({"nick": nick}, f)
    except Exception:
        pass  # Fail silently if we can't save


class HomeScreen(Screen):
    """Welcome screen for nickname and settings customization."""

    BINDINGS = [
        ("up", "nav_up", "Up"),
        ("down", "nav_down", "Down"),
        ("left", "adjust_left", "Left"),
        ("right", "adjust_right", "Right"),
        ("enter", "confirm", "Connect"),
    ]

    class SettingsConfirmed(Message):
        """Message sent when user confirms settings."""
        def __init__(self, nick: str, audio_enabled: bool, volume: float, server: dict):
            self.nick = nick
            self.audio_enabled = audio_enabled
            self.volume = volume
            self.server = server
            super().__init__()

    def __init__(self, config: dict = None, theme: str = "default", **kwargs):
        super().__init__(**kwargs)
        self.config = config or {}
        self.theme = theme
        self.servers = self.config.get("servers", [{"name": "Libera.Chat", "host": "irc.libera.chat", "port": 6667, "ssl": False, "nick": "phosphor_user", "channels": []}])
        self.selected_server_idx = 0
        # Load last used nickname, or fall back to config/default
        self.default_nick = _load_last_nick() or self.servers[0].get("nick", "phosphor_user")
        self.audio_config = self.config.get("audio", {"enabled": True, "volume": 0.5})
        self.current_volume = self.audio_config.get("volume", 0.5)
        self.audio_enabled = self.audio_config.get("enabled", True)
        self.current_nick = self.default_nick
        self.current_server = self.servers[0].get("host", "irc.libera.chat")  # Custom server input
        self.using_custom_server = False  # Track if user typed a custom server
        self.selected_row = 0  # 0=server, 1=nick, 2=audio, 3=volume
        self.total_rows = 4
        self.nick_error = ""  # Validation error message

    def _validate_nickname(self, nick: str) -> str:
        """Validate IRC nickname. Returns error message or empty string if valid."""
        import re
        if not nick:
            return "Nickname required"
        if len(nick) > 30:
            return "Max 30 characters"
        if nick[0].isdigit() or nick[0] == '-':
            return "Cannot start with digit or -"
        # IRC valid chars: letters, digits, and special: [ ] \ ^ _ { } |
        if not re.match(r'^[A-Za-z\[\]\\^_{}|][A-Za-z0-9\[\]\\^_{}|\-]*$', nick):
            return "Invalid characters"
        return ""

    def _render_volume_bar(self, disabled: bool = False) -> str:
        """Render ASCII volume bar."""
        if disabled:
            return "[──────────] ---% ".ljust(18)
        filled = int(self.current_volume * 10)
        bar = "█" * filled + "░" * (10 - filled)
        return f"[{bar}] {int(self.current_volume * 100):3d}%".ljust(18)

    def _render_audio_toggle(self) -> str:
        """Render ASCII audio toggle."""
        if self.audio_enabled:
            return "[cyan][ ON  ][/] OFF "
        else:
            return " ON  [cyan][ OFF ][/]"

    def _render_screen(self) -> str:
        """Render the entire retro screen."""
        # Theme-specific colors
        is_halloween = self.theme == "halloween"
        
        if is_halloween:
            border_color = "#ff6600"
            accent_color = "#ff9900"
            text_color = "#ffcc00"
            dim_color = "#996699"
            logo = LOGO_HALLOWEEN
            tagline = "[#9966ff]     🎃 Spooky IRC Terminal Magic 🎃[/]"
        else:
            border_color = "green"
            accent_color = "cyan"
            text_color = "white"
            dim_color = "dim"
            logo = LOGO
            tagline = "[cyan]     Modern IRC Client = Terminal Magic[/]"
        
        # Selection indicators
        sel = lambda i: ">" if self.selected_row == i else " "
        
        # Box width (internal content width, excluding borders)
        BOX_WIDTH = 47
        
        def format_row(selector, label, value, value_width, disabled=False):
            """Format a row with proper alignment inside the box."""
            prefix = f"  {selector} {label}:     "
            value_str = str(value).ljust(value_width)
            content_len = len(prefix) + len(value_str)
            padding = BOX_WIDTH - content_len
            spacer = " " * max(0, padding)
            sel_colored = f"[{accent_color}]{selector}[/]" if selector == ">" else " "
            value_color = f"[{dim_color}]" if disabled else f"[{accent_color}]"
            return f"[{border_color}]│[/]  {sel_colored} [{text_color}]{label}:[/]     {value_color}{value_str}[/]{spacer}[{border_color}]│[/]"
        
        # Server display - show custom server or preset with arrows
        if self.using_custom_server:
            server_display = self.current_server[:20].ljust(20)
        else:
            current_server = self.servers[self.selected_server_idx]
            server_name = current_server.get("name", current_server.get("host", "Unknown"))
            if len(self.servers) > 1:
                server_display = f"< {server_name[:16].ljust(16)} >"
            else:
                server_display = server_name[:20].ljust(20)
        
        # Pad values to fixed width
        nick_display = self.current_nick[:20].ljust(20)
        audio_display = "< ON  >" if self.audio_enabled else "< OFF >"
        vol_bar = self._render_volume_bar(disabled=not self.audio_enabled)
        
        # Empty row helper
        empty_row = f"[{border_color}]│[/]{' ' * BOX_WIDTH}[{border_color}]│[/]"
        
        # Error message line
        error_line = f"[red]{self.nick_error.center(47)}[/]" if self.nick_error else " " * 47
        
        # Halloween decorations
        if is_halloween:
            separator = "[#ff6600]═══🎃═══🦇═══💀═══🕷️═══🎃═══🦇═══💀═══🕷️═══🎃═══[/]"
            config_header = f"[{border_color}]┌────────────🎃 CONFIGURATION 🎃────────────┐[/]"
            config_footer = f"[{border_color}]└───────────────────────────────────────────────┘[/]"
            nav_hint = f"  [{border_color}]↑↓[/] Navigate   [{border_color}]←→[/] Adjust   [{border_color}]ENTER[/] Connect"
        else:
            separator = "[yellow]════════════════════════════════════════════════════[/]"
            config_header = f"[{border_color}]┌──────────────── CONFIGURATION ────────────────┐[/]"
            config_footer = f"[{border_color}]└───────────────────────────────────────────────┘[/]"
            nav_hint = f"  [{border_color}]↑↓[/] Navigate   [{border_color}]←→[/] Adjust   [{border_color}]ENTER[/] Connect"
        
        lines = [
            "",
            logo,
            separator,
            tagline,
            separator,
            "",
            config_header,
            empty_row,
            format_row(sel(0), "SERVER  ", server_display, 20),
            empty_row,
            format_row(sel(1), "NICKNAME", nick_display, 20),
            empty_row,
            format_row(sel(2), "AUDIO   ", audio_display, 7),
            empty_row,
            format_row(sel(3), "VOLUME  ", vol_bar, 18, disabled=not self.audio_enabled),
            empty_row,
            config_footer,
            error_line,
            separator,
            nav_hint,
            separator,
        ]
        return "\n".join(lines)

    def compose(self) -> ComposeResult:
        """Compose the home screen."""
        # Input value depends on selected row (0=server, 1=nick)
        initial_value = self.current_server if self.selected_row == 0 else self.current_nick
        yield Container(
            Static(self._render_screen(), id="retro-display"),
            Container(
                Input(value=initial_value, id="nick-input"),
                id="nick-container"
            ),
            id="home-container"
        )

    def on_mount(self):
        """Focus and setup."""
        # Apply theme class
        if self.theme == "halloween":
            self.add_class("halloween")
        self._update_display()

    def _update_display(self):
        """Update the retro display."""
        display = self.query_one("#retro-display", Static)
        display.update(self._render_screen())

    def on_input_changed(self, event: Input.Changed):
        """Update display when input changes (server or nickname)."""
        if self.selected_row == 0:  # Server row
            self.current_server = event.value or self.servers[0].get("host", "irc.libera.chat")
            self.using_custom_server = bool(event.value and event.value != self.servers[self.selected_server_idx].get("host", ""))
            self.nick_error = ""  # Clear error when editing server
        else:  # Nickname row
            self.current_nick = event.value or self.default_nick
            # Validate nickname as user types
            self.nick_error = self._validate_nickname(self.current_nick)
        self._update_display()

    def on_input_submitted(self, event: Input.Submitted):
        """Handle Enter in input."""
        self._confirm_settings()

    def _sync_input_to_row(self):
        """Update input field value to match the currently selected row."""
        nick_input = self.query_one("#nick-input", Input)
        if self.selected_row == 0:
            nick_input.value = self.current_server
        elif self.selected_row == 1:
            nick_input.value = self.current_nick
        # For rows 2 and 3 (audio/volume), input isn't used

    def action_nav_up(self):
        """Navigate up."""
        nick_input = self.query_one("#nick-input", Input)
        # Save current input value before navigating
        if self.selected_row == 0:
            self.current_server = nick_input.value or self.servers[0].get("host", "irc.libera.chat")
            self.using_custom_server = bool(nick_input.value and nick_input.value != self.servers[self.selected_server_idx].get("host", ""))
        elif self.selected_row == 1:
            self.current_nick = nick_input.value or self.default_nick
        if nick_input.has_focus:
            nick_input.blur()
        self.selected_row = (self.selected_row - 1) % self.total_rows
        self._sync_input_to_row()
        self._update_display()

    def action_nav_down(self):
        """Navigate down."""
        nick_input = self.query_one("#nick-input", Input)
        # Save current input value before navigating
        if self.selected_row == 0:
            self.current_server = nick_input.value or self.servers[0].get("host", "irc.libera.chat")
            self.using_custom_server = bool(nick_input.value and nick_input.value != self.servers[self.selected_server_idx].get("host", ""))
        elif self.selected_row == 1:
            self.current_nick = nick_input.value or self.default_nick
        if nick_input.has_focus:
            nick_input.blur()
        self.selected_row = (self.selected_row + 1) % self.total_rows
        self._sync_input_to_row()
        self._update_display()

    def action_adjust_left(self):
        """Handle left arrow - adjust current selection."""
        nick_input = self.query_one("#nick-input", Input)
        if nick_input.has_focus:
            return  # Let input handle cursor
        
        if self.selected_row == 0 and not self.using_custom_server:  # Server (only cycle if not custom)
            self.selected_server_idx = (self.selected_server_idx - 1) % len(self.servers)
            # Update server and nick to match
            self.current_server = self.servers[self.selected_server_idx].get("host", "irc.libera.chat")
            self.current_nick = self.servers[self.selected_server_idx].get("nick", "phosphor_user")
        elif self.selected_row == 2:  # Audio toggle
            self.audio_enabled = not self.audio_enabled
        elif self.selected_row == 3 and self.audio_enabled:  # Volume (only if audio on)
            self.current_volume = max(0.0, self.current_volume - 0.1)
        self._update_display()

    def action_adjust_right(self):
        """Handle right arrow - adjust current selection."""
        nick_input = self.query_one("#nick-input", Input)
        if nick_input.has_focus:
            return  # Let input handle cursor
        
        if self.selected_row == 0 and not self.using_custom_server:  # Server (only cycle if not custom)
            self.selected_server_idx = (self.selected_server_idx + 1) % len(self.servers)
            # Update server and nick to match
            self.current_server = self.servers[self.selected_server_idx].get("host", "irc.libera.chat")
            self.current_nick = self.servers[self.selected_server_idx].get("nick", "phosphor_user")
        elif self.selected_row == 2:  # Audio toggle
            self.audio_enabled = not self.audio_enabled
        elif self.selected_row == 3 and self.audio_enabled:  # Volume (only if audio on)
            self.current_volume = min(1.0, self.current_volume + 0.1)
        self._update_display()

    def action_confirm(self):
        """Confirm and connect."""
        self._confirm_settings()

    def on_key(self, event):
        """Handle key presses for server/nickname editing."""
        # Allow typing on server row (0) or nickname row (1)
        if self.selected_row in (0, 1) and event.key not in ("up", "down", "enter", "escape"):
            # For server row, also allow left/right if using custom server (for cursor movement)
            if self.selected_row == 0 and event.key in ("left", "right") and not self.using_custom_server:
                return  # Let adjust_left/right handle preset cycling
            nick_input = self.query_one("#nick-input", Input)
            if not nick_input.has_focus:
                # Set input value based on which row we're on
                if self.selected_row == 0:
                    nick_input.value = self.current_server
                else:
                    nick_input.value = self.current_nick
                nick_input.focus()

    def _confirm_settings(self):
        """Confirm settings and proceed."""
        nick = self.current_nick.strip() or self.default_nick
        
        # Validate nickname before proceeding
        self.nick_error = self._validate_nickname(nick)
        if self.nick_error:
            self._update_display()
            return  # Don't proceed with invalid nickname
        
        # Save the nickname for future use
        _save_last_nick(nick)
        
        # Build server config - use custom or preset
        if self.using_custom_server:
            # Parse custom server (format: host or host:port)
            server_str = self.current_server.strip()
            if ":" in server_str:
                host, port_str = server_str.rsplit(":", 1)
                try:
                    port = int(port_str)
                except ValueError:
                    port = 6667
            else:
                host = server_str
                port = 6667
            
            server = {
                "name": host,
                "host": host,
                "port": port,
                "ssl": port == 6697,  # Common SSL port
                "nick": nick,
                "channels": []
            }
        else:
            server = self.servers[self.selected_server_idx].copy()
            server["nick"] = nick  # Use the entered nick
        
        self.post_message(self.SettingsConfirmed(nick, self.audio_enabled, self.current_volume, server))


class TeletextScreen(Screen):
    """Retro Teletext dashboard screen - Page 100 (Ceefax style)."""

    BINDINGS = [("f1", "toggle_teletext", "Back to Chat")]

    def __init__(self, app_ref=None, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.update_task = None
        self.start_time = time.time()
        self.frame_count = 0
        self.blink_state = False
        self.ticker_offset = 0
        # Get theme from app
        self.theme = getattr(app_ref, 'active_theme', 'default') if app_ref else 'default'

    def compose(self) -> ComposeResult:
        """Compose the teletext screen."""
        yield Container(
            Static(self._generate_dashboard(), id="dashboard-content"),
            id="teletext-container"
        )

    def _get_dynamic_data(self) -> dict:
        """Get dynamic data from the app."""
        data = {
            "connected": False,
            "server": "Not connected",
            "nick": "Unknown",
            "channels": [],
            "current_channel": "#general",
            "users_count": 0,
            "messages_count": 0,
            "uptime": time.time() - self.start_time,
        }

        if self.app_ref:
            # Connection status
            data["connected"] = getattr(self.app_ref, "irc_connected", False)
            
            # Server info
            if hasattr(self.app_ref, "irc"):
                irc = self.app_ref.irc
                data["server"] = f"{irc.host}:{irc.port}"
                data["nick"] = getattr(irc, "nick", "Unknown")
            
            # Channels from config
            if hasattr(self.app_ref, "config"):
                servers = self.app_ref.config.get("servers", [])
                if servers:
                    data["channels"] = servers[0].get("channels", [])
            
            # Current channel
            data["current_channel"] = getattr(self.app_ref, "current_channel", "#general")

        return data

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        td = timedelta(seconds=int(seconds))
        hours, remainder = divmod(td.seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{td.days}d {hours:02d}:{minutes:02d}:{secs:02d}"

    def _generate_ticker(self, width: int = 50) -> str:
        """Generate scrolling news ticker."""
        data = self._get_dynamic_data()
        
        status = "CONNECTED" if data["connected"] else "DISCONNECTED"
        ticker_text = f"    STATUS: {status} | SERVER: {data['server']} | NICK: {data['nick']} | CHANNEL: {data['current_channel']} | UPTIME: {self._format_uptime(data['uptime'])}    "
        
        self.ticker_offset = (self.ticker_offset + 1) % len(ticker_text)
        scrolled = ticker_text[self.ticker_offset:] + ticker_text[:self.ticker_offset]
        return scrolled[:width]

    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
    
    def _get_system_stats(self) -> dict:
        """Get real-time system statistics."""
        stats = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "memory_used_gb": 0.0,
            "memory_total_gb": 0.0,
            "network_sent_mb": 0.0,
            "network_recv_mb": 0.0,
            "disk_usage_percent": 0.0,
        }
        
        try:
            import psutil
            
            # CPU usage
            stats["cpu_percent"] = psutil.cpu_percent(interval=0)
            
            # Memory usage
            mem = psutil.virtual_memory()
            stats["memory_percent"] = mem.percent
            stats["memory_used_gb"] = mem.used / (1024 ** 3)
            stats["memory_total_gb"] = mem.total / (1024 ** 3)
            
            # Network I/O
            net = psutil.net_io_counters()
            stats["network_sent_mb"] = net.bytes_sent / (1024 ** 2)
            stats["network_recv_mb"] = net.bytes_recv / (1024 ** 2)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            stats["disk_usage_percent"] = disk.percent
            
        except ImportError:
            pass
        
        return stats

    def _generate_dashboard(self) -> str:
        """Generate authentic Ceefax-style teletext dashboard."""
        self.frame_count += 1
        self.blink_state = not self.blink_state
        
        data = self._get_dynamic_data()
        stats = self._get_system_stats()

        timestamp = datetime.now().strftime("%H:%M:%S")
        day = datetime.now().strftime("%a")
        date = datetime.now().strftime("%d")
        month = datetime.now().strftime("%b")
        
        pid = os.getpid()
        mem_mb = self._get_memory_mb()
        session_uptime = self._format_uptime(data['uptime'])

        # Theme-specific colors
        is_halloween = self.theme == "halloween"
        
        if is_halloween:
            primary = "#ff6600"
            secondary = "#ff9900"
            accent = "#9966ff"
            text = "#ffcc00"
            highlight = "#ff6600"
            ticker_bg = "#4a2a4a"
        else:
            primary = "green"
            secondary = "cyan"
            accent = "yellow"
            text = "white"
            highlight = "yellow"
            ticker_bg = "blue"

        lines = []

        # Header line - PID, network stats, date and time
        header = f"PID:{pid}  [{secondary}]↑{stats['network_sent_mb']:.1f}MB ↓{stats['network_recv_mb']:.1f}MB[/]  {day} {date} {month}  [{secondary}]{timestamp}[/]"
        lines.append(f"[{text}]{header}[/]")
        lines.append("")

        # Logo banner - phosphor with highlighted middle P
        lines.append("")
        if is_halloween:
            lines.append(f"[{primary}]██████╗ ██╗  ██╗ ██████╗ ███████╗[/][{accent}]██████╗ [/][{primary}]██╗  ██╗ ██████╗ ██████╗ [/]")
            lines.append(f"[{primary}]██╔══██╗██║  ██║██╔═══██╗██╔════╝[/][{accent}]██╔══██╗[/][{primary}]██║  ██║██╔═══██╗██╔══██╗[/]")
            lines.append(f"[{secondary}]██████╔╝███████║██║   ██║███████╗[/][{accent}]██████╔╝[/][{secondary}]███████║██║   ██║██████╔╝[/]")
            lines.append(f"[{secondary}]██╔═══╝ ██╔══██║██║   ██║╚════██║[/][{accent}]██╔═══╝ [/][{secondary}]██╔══██║██║   ██║██╔══██╗[/]")
            lines.append(f"[{text}]██║     ██║  ██║╚██████╔╝███████║[/][{accent}]██║     [/][{text}]██║  ██║╚██████╔╝██║  ██║[/]")
            lines.append(f"[{text}]╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝[/][{accent}]╚═╝     [/][{text}]╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝[/]")
            lines.append("")
            lines.append(f"[{accent}]🎃 SPOOKY TELETEXT DASHBOARD 🎃[/]")
        else:
            lines.append("[green on black]██████╗ ██╗  ██╗ ██████╗ ███████╗[/][cyan on black]██████╗ [/][green on black]██╗  ██╗ ██████╗ ██████╗ [/]")
            lines.append("[green on black]██╔══██╗██║  ██║██╔═══██╗██╔════╝[/][cyan on black]██╔══██╗[/][green on black]██║  ██║██╔═══██╗██╔══██╗[/]")
            lines.append("[green on black]██████╔╝███████║██║   ██║███████╗[/][cyan on black]██████╔╝[/][green on black]███████║██║   ██║██████╔╝[/]")
            lines.append("[green on black]██╔═══╝ ██╔══██║██║   ██║╚════██║[/][cyan on black]██╔═══╝ [/][green on black]██╔══██║██║   ██║██╔══██╗[/]")
            lines.append("[green on black]██║     ██║  ██║╚██████╔╝███████║[/][cyan on black]██║     [/][green on black]██║  ██║╚██████╔╝██║  ██║[/]")
            lines.append("[green on black]╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝[/][cyan on black]╚═╝     [/][green on black]╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝[/]")
        lines.append("")

        # System Performance section - left-aligned, labels above bars
        if is_halloween:
            lines.append(f"[{primary}]🦇 SYSTEM PERFORMANCE 🦇[/]")
        else:
            lines.append(f"[{accent}]SYSTEM PERFORMANCE[/]")
        lines.append("")
        
        # CPU - label above, bar below, left-aligned
        cpu_bar = self._render_bar(stats["cpu_percent"], 100, 50)
        cpu_color = self._get_usage_color(stats["cpu_percent"], is_halloween)
        lines.append(f"[{text}]CPU {stats['cpu_percent']:5.1f}%[/]")
        lines.append(f"[{cpu_color}]{cpu_bar}[/]")
        lines.append("")
        
        # Program Memory - show program memory out of 2GB
        max_mem_gb = 2.0
        mem_percent = (mem_mb / 1024) / max_mem_gb * 100
        mem_bar = self._render_bar(mem_percent, 100, 50)
        mem_color = self._get_usage_color(mem_percent, is_halloween)
        lines.append(f"[{text}]Memory {mem_mb:.1f}MB / 2048MB[/] [{secondary}]({mem_percent:.1f}%)[/]")
        lines.append(f"[{mem_color}]{mem_bar}[/]")
        lines.append("")

        # Connection status section
        if is_halloween:
            lines.append(f"[{primary}]💀 IRC Connection 💀[/]")
        else:
            lines.append(f"[{primary}]IRC Connection[/]")
        lines.append(f"")
        
        if data["connected"]:
            if is_halloween:
                status_icon = f"[{primary}]🎃[/]" if self.blink_state else f"[{secondary}]👻[/]"
            else:
                status_icon = "[green]●[/]" if self.blink_state else "[green]○[/]"
            lines.append(f"[{accent}]CONNECTED TO SERVER[/] {status_icon}")
        else:
            if is_halloween:
                status_icon = "[red]💀[/]" if self.blink_state else "[red]☠️[/]"
            else:
                status_icon = "[red]●[/]" if self.blink_state else "[red]○[/]"
            lines.append(f"[{accent}]DISCONNECTED[/] {status_icon}")
        lines.append(f"")

        lines.append(f"[{text}]Server:[/]  [{secondary}]{data['server']}[/]")
        lines.append(f"[{text}]Nick:[/]    [{secondary}]{data['nick']}[/]")
        lines.append(f"[{text}]Session:[/] [{secondary}]{session_uptime}[/]")
        lines.append("")

        # Channels section - simplified
        if is_halloween:
            lines.append(f"[{primary}]🕷️ CHANNELS 🕷️[/]")
        else:
            lines.append(f"[{accent}]CHANNELS[/]")
        if data["channels"]:
            for channel in data["channels"][:5]:
                if is_halloween:
                    marker = f"[{primary}]🎃[/]" if channel == data["current_channel"] else " "
                else:
                    marker = f"[{accent}]►[/]" if channel == data["current_channel"] else " "
                lines.append(f"{marker} [{text}]{channel}[/]")
        else:
            lines.append(f"[{text}]No channels joined[/]")
        lines.append("")

        # Scrolling ticker
        ticker = self._generate_ticker(70)
        if is_halloween:
            lines.append(f"[{secondary} on {ticker_bg}] 🦇 {ticker} [/]")
        else:
            lines.append(f"[{accent} on {ticker_bg}] ▶ {ticker} [/]")
        lines.append("")

        # Simple footer
        if is_halloween:
            lines.append(f"[{secondary}]Press F1 to escape the haunted dashboard 👻[/]")
        else:
            lines.append(f"[{secondary}]Press F1 to return to chat[/]")

        return "\n".join(lines)
    
    def _render_bar(self, value: float, max_value: float, width: int = 20) -> str:
        """Render a progress bar with smooth gradient."""
        filled = (value / max_value) * width
        full_blocks = int(filled)
        partial = filled - full_blocks
        
        # Use block characters for smooth gradient
        bar = "█" * full_blocks
        
        # Add partial block for smoother appearance
        if full_blocks < width and partial > 0:
            if partial > 0.75:
                bar += "▓"
            elif partial > 0.5:
                bar += "▒"
            elif partial > 0.25:
                bar += "░"
            else:
                bar += "░"
            empty_blocks = width - full_blocks - 1
        else:
            empty_blocks = width - full_blocks
        
        bar += "░" * empty_blocks
        return f"[{bar}]"
    
    def _get_usage_color(self, percent: float, is_halloween: bool = False) -> str:
        """Get color based on usage percentage."""
        if is_halloween:
            if percent < 50:
                return "#66ff66"  # Ghostly green
            elif percent < 75:
                return "#ff9900"  # Pumpkin orange
            else:
                return "#ff3333"  # Blood red
        else:
            if percent < 50:
                return "green"
            elif percent < 75:
                return "yellow"
            else:
                return "red"

    async def _update_dashboard(self):
        """Periodically update the dashboard."""
        while True:
            try:
                dashboard_widget = self.query_one("#dashboard-content", Static)
                dashboard_widget.update(self._generate_dashboard())
                await asyncio.sleep(1)
            except Exception:
                break

    async def on_mount(self):
        """Start live updates when screen is mounted."""
        # Apply theme class
        if self.theme == "halloween":
            self.add_class("halloween")
        self.update_task = asyncio.create_task(self._update_dashboard())

    async def on_unmount(self):
        """Stop updates when screen is closed."""
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

    def action_toggle_teletext(self):
        """Return to chat screen."""
        self.app.pop_screen()


class KeysScreen(Screen):
    """Modal screen showing keyboard shortcuts and commands."""

    BINDINGS = [
        ("escape", "close", "Close"),
    ]

    DEFAULT_CSS = """
    KeysScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.9);
    }
    
    KeysScreen > Static {
        width: auto;
        height: auto;
        background: #1a1a2e;
        padding: 1 3;
        border: solid #5865F2;
    }
    
    KeysScreen.halloween {
        background: rgba(26, 10, 26, 0.95);
    }
    
    KeysScreen.halloween > Static {
        background: #2d1f2d;
        border: solid #ff6600;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the keys screen."""
        yield Static(self._render_help())

    def on_mount(self):
        """Apply theme on mount."""
        if hasattr(self.app, 'active_theme') and self.app.active_theme == "halloween":
            self.add_class("halloween")

    def _render_help(self) -> str:
        """Render all help content."""
        # Check theme
        is_halloween = hasattr(self.app, 'active_theme') and self.app.active_theme == "halloween"
        
        if is_halloween:
            header_color = "#ff6600"
            section_color = "#9966ff"
            key_color = "#ff9900"
            cmd_color = "#ffcc00"
            text_color = "#ffcc00"
            dim_color = "#996699"
        else:
            header_color = "yellow"
            section_color = "magenta"
            key_color = "green"
            cmd_color = "yellow"
            text_color = "white"
            dim_color = "dim"
        
        lines = []
        
        # Header
        if is_halloween:
            lines.append(f"[bold {header_color}]🎃 PHOSPHOR HELP & SHORTCUTS 🎃[/]")
        else:
            lines.append(f"[bold {header_color}]PHOSPHOR HELP & SHORTCUTS[/]")
        lines.append("")
        
        # Keyboard shortcuts section
        if is_halloween:
            lines.append(f"[bold {section_color}]🦇 KEYBOARD SHORTCUTS 🦇[/]")
        else:
            lines.append(f"[bold {section_color}]KEYBOARD SHORTCUTS[/]")
        
        shortcuts = [
            ("F1", "Toggle Teletext Dashboard"),
            ("Ctrl+P", "Open Command Palette"),
            ("Ctrl+J", "Search/Join Channels"),
            ("Ctrl+B", "Bookmark Current Channel"),
            ("?", "Show This Help Screen"),
            ("Ctrl+C", "Quit Application"),
            ("←/→", "Navigate Between Sections"),
            ("/", "Focus Message Input"),
            ("Ctrl+/", "Unfocus Input"),
            ("↑/↓", "Navigate Lists"),
            ("Tab", "Auto-complete Command"),
            ("Enter", "Send Message / Confirm"),
            ("ESC", "Close Dialogs / Cancel"),
        ]
        
        for key, desc in shortcuts:
            lines.append(f"  [{key_color}]{key:12}[/] [{text_color}]{desc}[/]")
        
        lines.append("")
        
        # Slash commands section
        if is_halloween:
            lines.append(f"[bold {section_color}]💀 SLASH COMMANDS 💀[/] [{dim_color}](type in message input)[/]")
        else:
            lines.append(f"[bold {section_color}]SLASH COMMANDS[/] [{dim_color}](type in message input)[/]")
        
        commands = [
            ("/join #channel", "Join a channel"),
            ("/msg nick text", "Send direct message"),
            ("/dm nick", "Start DM conversation"),
            ("/close", "Close current DM"),
            ("/bookmark", "Bookmark current channel"),
            ("/unbookmark", "Remove channel bookmark"),
            ("/bookmarks", "List all bookmarks"),
            ("/send filepath", "Send file via wormhole"),
            ("/grab code", "Receive file via wormhole"),
            ("/ai question", "Ask AI assistant"),
        ]
        
        for cmd, desc in commands:
            lines.append(f"  [{cmd_color}]{cmd:16}[/] [{text_color}]{desc}[/]")
        
        lines.append("")
        
        # Command palette section
        if is_halloween:
            lines.append(f"[bold {section_color}]🕷️ COMMAND PALETTE 🕷️[/] [{dim_color}](Ctrl+P)[/]")
        else:
            lines.append(f"[bold {section_color}]COMMAND PALETTE[/] [{dim_color}](Ctrl+P)[/]")
        lines.append(f"  [{text_color}]Show Keyboard Shortcuts[/]")
        lines.append(f"  [{text_color}]Adjust Volume[/]")
        lines.append(f"  [{text_color}]Toggle Teletext Dashboard[/]")
        lines.append(f"  [{text_color}]Search Channels[/]")
        lines.append(f"  [{text_color}]Toggle Bookmark[/]")
        lines.append(f"  [{text_color}]Theme: Default / Halloween 🎃[/]")
        lines.append("")
        
        # Footer
        if is_halloween:
            lines.append(f"[{dim_color}]Press ESC to escape... if you dare 👻[/]")
        else:
            lines.append(f"[{dim_color}]Press ESC to close[/]")
        
        return "\n".join(lines)

    def action_close(self):
        """Close the keys screen."""
        self.app.pop_screen()


class VolumeScreen(Screen):
    """Modal screen for adjusting audio volume."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("left", "decrease_volume", "Decrease"),
        ("right", "increase_volume", "Increase"),
        ("up", "increase_volume", "Increase"),
        ("down", "decrease_volume", "Decrease"),
        ("m", "toggle_mute", "Mute"),
        ("enter", "close", "Confirm"),
    ]

    DEFAULT_CSS = """
    VolumeScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.9);
    }
    
    VolumeScreen > Static {
        width: auto;
        height: auto;
        background: #1a1a2e;
        padding: 2 4;
        border: solid #5865F2;
    }
    
    VolumeScreen.halloween {
        background: rgba(26, 10, 26, 0.95);
    }
    
    VolumeScreen.halloween > Static {
        background: #2d1f2d;
        border: solid #ff6600;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.volume = 0.5
        self.audio_enabled = True
        self._load_settings()

    def _load_settings(self):
        """Load current audio settings from app."""
        if hasattr(self.app, 'audio') and self.app.audio:
            self.volume = getattr(self.app.audio, 'volume', 0.5)
            self.audio_enabled = getattr(self.app.audio, 'enabled', True)

    def compose(self) -> ComposeResult:
        """Compose the volume screen."""
        yield Static(self._render_volume(), id="volume-content")

    def on_mount(self):
        """Load settings when mounted."""
        # Apply theme
        if hasattr(self.app, 'active_theme') and self.app.active_theme == "halloween":
            self.add_class("halloween")
        self._load_settings()
        self._update_display()

    def _render_volume_bar(self) -> str:
        """Render the volume bar."""
        is_halloween = hasattr(self.app, 'active_theme') and self.app.active_theme == "halloween"
        
        if not self.audio_enabled:
            if is_halloween:
                return "[#996699]░░░░░░░░░░░░░░░░░░░░[/] [red]💀 MUTED[/]"
            return "[dim]░░░░░░░░░░░░░░░░░░░░[/] [red]MUTED[/]"
        
        filled = int(self.volume * 20)
        bar = "█" * filled + "░" * (20 - filled)
        percent = int(self.volume * 100)
        
        # Color based on volume level
        if is_halloween:
            if percent < 30:
                color = "#66ff66"
            elif percent < 70:
                color = "#ff9900"
            else:
                color = "#ff3333"
            text_color = "#ffcc00"
        else:
            if percent < 30:
                color = "green"
            elif percent < 70:
                color = "yellow"
            else:
                color = "red"
            text_color = "white"
        
        return f"[{color}]{bar}[/] [{text_color}]{percent:3d}%[/]"

    def _render_volume(self) -> str:
        """Render the volume control UI."""
        is_halloween = hasattr(self.app, 'active_theme') and self.app.active_theme == "halloween"
        
        if is_halloween:
            header_color = "#ff6600"
            text_color = "#ffcc00"
            dim_color = "#996699"
            on_icon = "🎃"
            off_icon = "💀"
        else:
            header_color = "yellow"
            text_color = "white"
            dim_color = "dim"
            on_icon = "●"
            off_icon = "●"
        
        lines = []
        
        if is_halloween:
            lines.append(f"[bold {header_color}]🔊 VOLUME CONTROL 🔊[/]")
        else:
            lines.append(f"[bold {header_color}]VOLUME CONTROL[/]")
        lines.append("")
        lines.append(self._render_volume_bar())
        lines.append("")
        
        # Audio toggle
        if self.audio_enabled:
            if is_halloween:
                lines.append(f"[#66ff66]{on_icon}[/] [{text_color}]Audio ON[/]")
            else:
                lines.append(f"[green]{on_icon}[/] [{text_color}]Audio ON[/]")
        else:
            lines.append(f"[red]{off_icon}[/] [{text_color}]Audio OFF (Muted)[/]")
        
        lines.append("")
        lines.append(f"[{dim_color}]←/→ or ↑/↓[/]  [{text_color}]Adjust volume[/]")
        lines.append(f"[{dim_color}]M[/]          [{text_color}]Toggle mute[/]")
        lines.append(f"[{dim_color}]ESC/Enter[/]  [{text_color}]Close[/]")
        
        return "\n".join(lines)

    def _update_display(self):
        """Update the display."""
        try:
            content = self.query_one("#volume-content", Static)
            content.update(self._render_volume())
        except Exception:
            pass

    def _apply_volume(self):
        """Apply volume changes to the app's audio engine."""
        if hasattr(self.app, 'audio') and self.app.audio:
            self.app.audio.volume = self.volume
            self.app.audio.enabled = self.audio_enabled

    def action_increase_volume(self):
        """Increase volume by 10%."""
        if self.audio_enabled:
            self.volume = min(1.0, self.volume + 0.1)
            self._apply_volume()
            self._update_display()

    def action_decrease_volume(self):
        """Decrease volume by 10%."""
        if self.audio_enabled:
            self.volume = max(0.0, self.volume - 0.1)
            self._apply_volume()
            self._update_display()

    def action_toggle_mute(self):
        """Toggle audio mute."""
        self.audio_enabled = not self.audio_enabled
        self._apply_volume()
        self._update_display()

    def action_close(self):
        """Close the volume screen."""
        self.app.pop_screen()
