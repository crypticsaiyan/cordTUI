"""Embed widget - Rich message cards."""

from textual.widgets import Static
from textual.containers import Container


class Embed(Container):
    """A rich message embed card."""
    
    def __init__(self, title: str, description: str, color: str = "blurple", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.description = description
        self.color = color
        self.add_class("embed")
        
        if color == "success":
            self.add_class("embed-success")
        elif color == "error":
            self.add_class("embed-error")
    
    def compose(self):
        """Compose the embed."""
        yield Static(f"[bold]{self.title}[/bold]")
        yield Static(self.description)
