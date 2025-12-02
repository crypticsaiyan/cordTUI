"""Screen definitions for different views."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Static, Header, Footer
import plotext as plt


class TeletextScreen(Screen):
    """Retro Teletext dashboard screen."""
    
    BINDINGS = [("f1", "toggle_teletext", "Back to Chat")]
    
    def __init__(self, mcp_client=None, **kwargs):
        super().__init__(**kwargs)
        self.mcp_client = mcp_client
        self.add_class("teletext")
    
    def compose(self) -> ComposeResult:
        """Compose the teletext screen."""
        yield Header()
        yield Static("===== PAGE 100 ===== CORD-TUI SYSTEM MONITOR =====", classes="teletext-header")
        yield Container(
            Static(self._generate_dashboard(), id="dashboard-content"),
            id="teletext-container"
        )
        yield Footer()
    
    def _generate_dashboard(self) -> str:
        """Generate the teletext dashboard content."""
        # Create ASCII bar chart using plotext
        plt.clear_figure()
        plt.theme('dark')
        
        # Sample data
        services = ["API", "DB", "Cache", "Queue"]
        cpu = [45, 78, 23, 12]
        
        plt.simple_bar(services, cpu, width=50, title="CPU Usage (%)")
        chart = plt.build()
        
        # Add retro styling (no markup, just plain text for stability)
        output = "\n" + "="*50 + "\n"
        output += "SYSTEM STATUS: OPERATIONAL\n"
        output += "="*50 + "\n\n"
        output += chart
        output += "\n\nMEMORY: 4.2GB / 16GB"
        output += "\nNETWORK: 125 Mbps ↓ / 45 Mbps ↑"
        output += "\nUPTIME: 42 days, 13:37:00"
        output += "\n\nPress F1 to return to chat"
        
        return output
    
    async def on_mount(self):
        """Update dashboard with live data."""
        if self.mcp_client:
            stats = await self.mcp_client.execute("docker-stats")
            # TODO: Update dashboard with real stats
    
    def action_toggle_teletext(self):
        """Return to chat screen."""
        self.app.pop_screen()
