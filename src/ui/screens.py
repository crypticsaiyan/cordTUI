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


def _load_last_nick() -> str:
    """Load the last used nickname from settings."""
    settings_path = Path(".phosphor/last_nick.json")
    if settings_path.exists():
        try:
            with open(settings_path) as f:
                data = json.load(f)
                return data.get("nick", "cord_user")
        except Exception:
            pass
    return "cord_user"


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

    def __init__(self, config: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or {}
        self.servers = self.config.get("servers", [{"name": "Libera.Chat", "host": "irc.libera.chat", "port": 6667, "ssl": False, "nick": "cord_user", "channels": []}])
        self.selected_server_idx = 0
        # Load last used nickname, or fall back to config/default
        self.default_nick = _load_last_nick() or self.servers[0].get("nick", "cord_user")
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
            sel_colored = f"[cyan]{selector}[/]" if selector == ">" else " "
            value_color = "[dim]" if disabled else "[cyan]"
            return f"[green]│[/]  {sel_colored} [white]{label}:[/]     {value_color}{value_str}[/]{spacer}[green]│[/]"
        
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
        empty_row = f"[green]│[/]{' ' * BOX_WIDTH}[green]│[/]"
        
        # Error message line
        error_line = f"[red]{self.nick_error.center(47)}[/]" if self.nick_error else " " * 47
        
        lines = [
            "",
            LOGO,
            "[yellow]════════════════════════════════════════════════════[/]",
            "[cyan]     Discord UX + IRC Protocol = Terminal Magic[/]",
            "[yellow]════════════════════════════════════════════════════[/]",
            "",
            "[green]┌──────────────── CONFIGURATION ────────────────┐[/]",
            empty_row,
            format_row(sel(0), "SERVER  ", server_display, 20),
            empty_row,
            format_row(sel(1), "NICKNAME", nick_display, 20),
            empty_row,
            format_row(sel(2), "AUDIO   ", audio_display, 7),
            empty_row,
            format_row(sel(3), "VOLUME  ", vol_bar, 18, disabled=not self.audio_enabled),
            empty_row,
            "[green]└───────────────────────────────────────────────┘[/]",
            error_line,
            "[yellow]────────────────────────────────────────────────────[/]",
            "  [green]↑↓[/] Navigate   [green]←→[/] Adjust   [green]ENTER[/] Connect",
            "[yellow]────────────────────────────────────────────────────[/]",
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
            self.current_nick = self.servers[self.selected_server_idx].get("nick", "cord_user")
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
            self.current_nick = self.servers[self.selected_server_idx].get("nick", "cord_user")
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

        lines = []

        # Header line - PID, network stats, date and time
        header = f"PID:{pid}  [cyan]↑{stats['network_sent_mb']:.1f}MB ↓{stats['network_recv_mb']:.1f}MB[/]  {day} {date} {month}  [cyan]{timestamp}[/]"
        lines.append(f"[white]{header}[/]")
        lines.append("")

        # Logo banner - phosphor with highlighted middle P
        lines.append("")
        lines.append("[green on black]██████╗ ██╗  ██╗ ██████╗ ███████╗[/][cyan on black]██████╗ [/][green on black]██╗  ██╗ ██████╗ ██████╗ [/]")
        lines.append("[green on black]██╔══██╗██║  ██║██╔═══██╗██╔════╝[/][cyan on black]██╔══██╗[/][green on black]██║  ██║██╔═══██╗██╔══██╗[/]")
        lines.append("[green on black]██████╔╝███████║██║   ██║███████╗[/][cyan on black]██████╔╝[/][green on black]███████║██║   ██║██████╔╝[/]")
        lines.append("[green on black]██╔═══╝ ██╔══██║██║   ██║╚════██║[/][cyan on black]██╔═══╝ [/][green on black]██╔══██║██║   ██║██╔══██╗[/]")
        lines.append("[green on black]██║     ██║  ██║╚██████╔╝███████║[/][cyan on black]██║     [/][green on black]██║  ██║╚██████╔╝██║  ██║[/]")
        lines.append("[green on black]╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝[/][cyan on black]╚═╝     [/][green on black]╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝[/]")
        lines.append("")

        # System Performance section - left-aligned, labels above bars
        lines.append(f"[yellow]SYSTEM PERFORMANCE[/]")
        lines.append("")
        
        # CPU - label above, bar below, left-aligned
        cpu_bar = self._render_bar(stats["cpu_percent"], 100, 50)
        cpu_color = self._get_usage_color(stats["cpu_percent"])
        lines.append(f"[white]CPU {stats['cpu_percent']:5.1f}%[/]")
        lines.append(f"[{cpu_color}]{cpu_bar}[/]")
        lines.append("")
        
        # Program Memory - show program memory out of 2GB
        max_mem_gb = 2.0
        mem_percent = (mem_mb / 1024) / max_mem_gb * 100
        mem_bar = self._render_bar(mem_percent, 100, 50)
        mem_color = self._get_usage_color(mem_percent)
        lines.append(f"[white]Memory {mem_mb:.1f}MB / 2048MB[/] [cyan]({mem_percent:.1f}%)[/]")
        lines.append(f"[{mem_color}]{mem_bar}[/]")
        lines.append("")

        # Connection status section
        lines.append(f"[green]IRC Connection[/]")
        lines.append(f"")
        
        if data["connected"]:
            status_icon = "[green]●[/]" if self.blink_state else "[green]○[/]"
            lines.append(f"[yellow]CONNECTED TO SERVER[/] {status_icon}")
        else:
            status_icon = "[red]●[/]" if self.blink_state else "[red]○[/]"
            lines.append(f"[yellow]DISCONNECTED[/] {status_icon}")
        lines.append(f"")

        lines.append(f"[white]Server:[/]  [cyan]{data['server']}[/]")
        lines.append(f"[white]Nick:[/]    [cyan]{data['nick']}[/]")
        lines.append(f"[white]Session:[/] [cyan]{session_uptime}[/]")
        lines.append("")

        # Channels section - simplified
        lines.append(f"[yellow]CHANNELS[/]")
        if data["channels"]:
            for channel in data["channels"][:5]:
                marker = "[yellow]►[/]" if channel == data["current_channel"] else " "
                lines.append(f"{marker} [white]{channel}[/]")
        else:
            lines.append("[white]No channels joined[/]")
        lines.append("")

        # Scrolling ticker
        ticker = self._generate_ticker(70)
        lines.append(f"[yellow on blue] ▶ {ticker} [/]")
        lines.append("")

        # Simple footer
        lines.append("[cyan]Press F1 to return to chat[/]")

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
    
    def _get_usage_color(self, percent: float) -> str:
        """Get color based on usage percentage."""
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
