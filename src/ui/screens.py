"""Screen definitions for different views."""

import asyncio
import time
import os
import subprocess
from datetime import datetime, timedelta
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Static


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

    def _generate_dashboard(self) -> str:
        """Generate authentic Ceefax-style teletext dashboard."""
        self.frame_count += 1
        self.blink_state = not self.blink_state
        
        data = self._get_dynamic_data()

        timestamp = datetime.now().strftime("%H:%M/%S")
        day = datetime.now().strftime("%a")
        date = datetime.now().strftime("%d")
        month = datetime.now().strftime("%b")
        
        pid = os.getpid()
        mem_mb = self._get_memory_mb()

        lines = []

        # Header line - PID, memory, date and time
        header = f"PID:{pid}  MEM:{mem_mb:.1f}MB  {day} {date} {month}  [cyan]{timestamp}[/]"
        lines.append(f"[white]{header}[/]")
        lines.append("")

        # Logo banner
        lines.append("")
        lines.append("[white on black] ██████╗  ██████╗  ██████╗  ██████╗   [/][yellow on blue]                             [/]")
        lines.append("[white on black] ██╔════╝ ██╔═══██╗██╔══██╗██╔═══██╗  [/][yellow on blue]   ██████╗ ██████╗ ███████╗  [/]")
        lines.append("[white on black] ██║      ██║   ██║██████╔╝██║   ██║  [/][yellow on blue]  ██╔═══██╗██╔══██╗██╔════╝  [/]")
        lines.append("[white on black] ██║      ██║   ██║██╔══██╗██║   ██║  [/][yellow on blue]  ██║   ██║██████╔╝███████╗  [/]")
        lines.append("[white on black] ╚██████╗ ╚██████╔╝██║  ██║╚██████╔╝  [/][yellow on blue]  ╚██████╔╝██╔═══╝ ╚════██║  [/]")
        lines.append("[white on black]  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝   [/][yellow on blue]   ╚═════╝ ██║     ███████║  [/]")
        lines.append("[white on black]                                      [/][yellow on blue]           ╚═╝     ╚══════╝  [/]")
        lines.append("")

        # Connection status section
        lines.append(f"[green]Status[/]")
        lines.append(f"")
        
        if data["connected"]:
            status_icon = "[green]●[/]" if self.blink_state else "[green]○[/]"
            lines.append(f"[yellow]CONNECTED TO IRC SERVER[/] {status_icon}")
        else:
            status_icon = "[red]●[/]" if self.blink_state else "[red]○[/]"
            lines.append(f"[yellow]DISCONNECTED FROM SERVER[/] {status_icon}")
        lines.append(f"")

        lines.append(f"[white]Server:[/] [cyan]{data['server']}[/]")
        lines.append(f"[white]Nick:[/]   [cyan]{data['nick']}[/]")
        lines.append(f"[white]Uptime:[/] [cyan]{self._format_uptime(data['uptime'])}[/]")
        lines.append("")

        # Channels section
        lines.append(f"[green]Channels[/]")
        if data["channels"]:
            for i, channel in enumerate(data["channels"][:5]):
                marker = "[yellow]►[/]" if channel == data["current_channel"] else " "
                lines.append(f" {marker} [white]{channel:<20}[/][cyan]{160 + i}[/]")
        else:
            lines.append("[white]  No channels joined[/]")
        lines.append("")

        # Scrolling ticker
        ticker = self._generate_ticker(50)
        lines.append(f"[yellow on blue] ▶ {ticker} [/]")
        lines.append("")

        # Footer with colored buttons
        lines.append("[red]F1 Back[/]      [green]Channels[/]       [yellow]Transfer[/]        [cyan]A-Z Index[/]")

        return "\n".join(lines)

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
