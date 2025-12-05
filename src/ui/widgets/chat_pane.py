"""Chat pane widget - the center message stream."""

from datetime import datetime
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Static, Markdown

from src.ui.widgets.user_colors import format_username_colored


class ChatPane(VerticalScroll):
    """The main chat message stream."""
    
    can_focus = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Store messages per channel: {channel: [(author, content, is_system, timestamp), ...]}
        self.channel_messages = {}
        # Store DM messages: {nick: [(author, content, is_system, timestamp), ...]}
        self.dm_messages = {}
        self.current_channel = None
        self.current_dm = None  # Currently viewing DM with this nick
        self.current_nick = None  # The current user's IRC nick
    
    def _get_timestamp(self) -> str:
        """Get current time formatted as HH:MM."""
        return datetime.now().strftime("%H:%M")
    
    def _create_message_widget(self, author: str, content: str, is_system: bool, timestamp: str) -> Horizontal:
        """Create a message row widget with content and timestamp."""
        if is_system:
            content_widget = Static(f"[italic yellow]⚙ {content}[/]", classes="message-content system-message")
        else:
            # Use colored username with Rich markup
            colored_author = format_username_colored(author)
            # Add (you) indicator if this is the current user
            if self.current_nick and author == self.current_nick:
                content_widget = Static(f"{colored_author} (you): {content}", classes="message-content message")
            else:
                content_widget = Static(f"{colored_author}: {content}", classes="message-content message")
        
        time_widget = Static(f"[dim]{timestamp}[/]", classes="message-time")
        
        return Horizontal(content_widget, time_widget, classes="message-row")
    
    def add_message(self, author: str, content: str, is_system: bool = False, channel: str = None, dm_nick: str = None):
        """Add a message to the chat.
        
        Args:
            author: Message author
            content: Message content
            is_system: Whether this is a system message
            channel: Channel name (for channel messages)
            dm_nick: Nick of the DM partner (for DM messages)
        """
        # Strip leading colon from content if present (IRC protocol artifact)
        content = content.lstrip(": ")
        
        # Get current timestamp
        timestamp = self._get_timestamp()
        
        # Store message in history
        if dm_nick:
            # DM message
            if dm_nick not in self.dm_messages:
                self.dm_messages[dm_nick] = []
            self.dm_messages[dm_nick].append((author, content, is_system, timestamp))
            
            # Only display if viewing this DM conversation
            if dm_nick == self.current_dm:
                msg_widget = self._create_message_widget(author, content, is_system, timestamp)
                self.mount(msg_widget)
                self.scroll_end(animate=False)
        elif channel:
            # Channel message
            if channel not in self.channel_messages:
                self.channel_messages[channel] = []
            self.channel_messages[channel].append((author, content, is_system, timestamp))
            
            # Only display if it's for the current channel
            if channel == self.current_channel:
                msg_widget = self._create_message_widget(author, content, is_system, timestamp)
                self.mount(msg_widget)
                self.scroll_end(animate=False)
        else:
            # System message with no target - show if in current view
            msg_widget = self._create_message_widget(author, content, is_system, timestamp)
            self.mount(msg_widget)
            self.scroll_end(animate=False)
    
    def switch_channel(self, channel: str):
        """Switch to a different channel and restore its message history."""
        self.current_channel = channel
        self.current_dm = None  # Clear DM view
        
        # Clear current display
        self.remove_children()
        
        # Restore messages for this channel
        if channel in self.channel_messages:
            for msg_data in self.channel_messages[channel]:
                # Handle both old format (3 items) and new format (4 items with timestamp)
                if len(msg_data) == 4:
                    author, content, is_system, timestamp = msg_data
                else:
                    author, content, is_system = msg_data
                    timestamp = "--:--"  # Placeholder for old messages without timestamp
                
                msg_widget = self._create_message_widget(author, content, is_system, timestamp)
                self.mount(msg_widget)
        
        self.scroll_end(animate=False)
    
    def switch_dm(self, nick: str):
        """Switch to a DM conversation and restore its message history."""
        self.current_dm = nick
        self.current_channel = None  # Clear channel view
        
        # Clear current display
        self.remove_children()
        
        # Restore messages for this DM
        if nick in self.dm_messages:
            for msg_data in self.dm_messages[nick]:
                if len(msg_data) == 4:
                    author, content, is_system, timestamp = msg_data
                else:
                    author, content, is_system = msg_data
                    timestamp = "--:--"
                
                msg_widget = self._create_message_widget(author, content, is_system, timestamp)
                self.mount(msg_widget)
        
        self.scroll_end(animate=False)
    
    def add_embed(self, title: str, content: str, embed_type: str = "info"):
        """Add a rich embed card."""
        embed_content = f"**{title}**\n\n{content}"
        embed_widget = Markdown(embed_content)
        embed_widget.add_class("embed")
        
        if embed_type == "success":
            embed_widget.add_class("embed-success")
        elif embed_type == "error":
            embed_widget.add_class("embed-error")
        
        self.mount(embed_widget)
        self.scroll_end(animate=False)
