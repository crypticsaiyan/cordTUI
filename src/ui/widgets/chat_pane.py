"""Chat pane widget - the center message stream."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static, Markdown
from textual.reactive import reactive


class ChatPane(VerticalScroll):
    """The main chat message stream."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Store messages per channel: {channel: [(author, content, is_system), ...]}
        self.channel_messages = {}
        self.current_channel = None
    
    def add_message(self, author: str, content: str, is_system: bool = False, channel: str = None):
        """Add a message to the chat."""
        # Store message in history
        if channel:
            if channel not in self.channel_messages:
                self.channel_messages[channel] = []
            self.channel_messages[channel].append((author, content, is_system))
        
        # Only display if it's for the current channel or no channel specified (system messages)
        if channel is None or channel == self.current_channel:
            if is_system:
                msg_widget = Static(f"[italic yellow]⚙ {content}[/]", classes="system-message")
            else:
                msg_widget = Markdown(f"**{author}**: {content}")
                msg_widget.add_class("message")
            
            self.mount(msg_widget)
            self.scroll_end(animate=False)
    
    def switch_channel(self, channel: str):
        """Switch to a different channel and restore its message history."""
        self.current_channel = channel
        
        # Clear current display
        self.remove_children()
        
        # Restore messages for this channel
        if channel in self.channel_messages:
            for author, content, is_system in self.channel_messages[channel]:
                if is_system:
                    msg_widget = Static(f"[italic yellow]⚙ {content}[/]", classes="system-message")
                else:
                    msg_widget = Markdown(f"**{author}**: {content}")
                    msg_widget.add_class("message")
                self.mount(msg_widget)
        
        self.scroll_end(animate=False)
    
    def add_embed(self, title: str, content: str, embed_type: str = "info"):
        """Add a Discord-style embed card."""
        embed_content = f"**{title}**\n\n{content}"
        embed_widget = Markdown(embed_content)
        embed_widget.add_class("embed")
        
        if embed_type == "success":
            embed_widget.add_class("embed-success")
        elif embed_type == "error":
            embed_widget.add_class("embed-error")
        
        self.mount(embed_widget)
        self.scroll_end(animate=False)
