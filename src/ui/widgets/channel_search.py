"""Channel search and join dialog with intelligent suggestions."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Input, ListView, ListItem, Label, Button
from textual.screen import ModalScreen
from textual.message import Message
from textual.binding import Binding
import re
from typing import List, Dict, Set


class ChannelSearchScreen(ModalScreen):
    """Modal screen for searching and joining channels."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", show=False),
    ]
    
    class ChannelSelected(Message):
        """Message posted when a channel is selected."""
        def __init__(self, channel: str):
            super().__init__()
            self.channel = channel
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.recent_channels = set()  # Recently joined channels
        self.popular_channels = [  # Common IRC channels
            "#general", "#random", "#help", "#programming", "#python", 
            "#javascript", "#linux", "#gaming", "#music", "#news"
        ]
    
    def compose(self) -> ComposeResult:
        """Compose the channel search dialog."""
        with Container(id="channel-search-dialog"):
            yield Static("Join Channel", classes="dialog-title")
            
            with Vertical():
                yield Input(
                    placeholder="Type channel name and press Enter...",
                    id="channel-search-input"
                )
                
                yield Static("Suggestions:", classes="section-header")
                yield ListView(id="suggestions-list")
                
                with Horizontal():
                    yield Button("Cancel", id="cancel-btn")
    
    def on_mount(self):
        """Focus the input when mounted."""
        self.query_one("#channel-search-input", Input).focus()
        self.update_suggestions("")
    
    def on_input_changed(self, event: Input.Changed):
        """Update suggestions as user types."""
        if event.input.id == "channel-search-input":
            search_term = event.value
            self.update_suggestions(search_term)
    
    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.dismiss()
    
    def on_input_submitted(self, event: Input.Submitted):
        """Handle enter key in search input."""
        if event.input.id == "channel-search-input":
            # Prevent the event from bubbling up to the main app
            event.prevent_default()
            event.stop()
            
            channel_name = event.value.strip()
            if channel_name:
                if not channel_name.startswith('#'):
                    channel_name = '#' + channel_name
                self.post_message(self.ChannelSelected(channel_name))
                self.dismiss()
    

    
    def update_suggestions(self, search_term: str):
        """Update suggestions based on search term."""
        suggestions_list = self.query_one("#suggestions-list", ListView)
        suggestions_list.clear()
        
        suggestions = self._generate_suggestions(search_term)
        
        if not suggestions:
            suggestions_list.append(ListItem(Label("💡 Start typing to see suggestions")))
            return
        
        for suggestion in suggestions[:8]:  # Limit to 8 suggestions
            item = ListItem(Label(f"💡 {suggestion}"), classes="suggestion-item")
            item.suggestion_text = suggestion
            suggestions_list.append(item)
    
    def _generate_suggestions(self, search_term: str) -> List[str]:
        """Generate intelligent suggestions based on search term."""
        if not search_term:
            # Show popular channels when no search term
            return self.popular_channels[:5]
        
        suggestions = []
        search_lower = search_term.lower()
        
        # Add exact match suggestion if not already a channel name
        if not search_term.startswith('#'):
            suggestions.append(f"#{search_term}")
        
        # Add popular channels that match
        for channel in self.popular_channels:
            if search_lower in channel.lower() and channel not in suggestions:
                suggestions.append(channel)
        
        # Add recent channels that match
        for channel in self.recent_channels:
            if search_lower in channel.lower() and channel not in suggestions:
                suggestions.append(channel)
        
        # Add variations and common patterns
        if len(search_term) >= 2:
            variations = [
                f"#{search_term}-dev",
                f"#{search_term}-help", 
                f"#{search_term}-general",
                f"#{search_term}-chat",
                f"#{search_term}s",  # plural
            ]
            
            for variation in variations:
                if variation not in suggestions:
                    suggestions.append(variation)
        
        return suggestions
    
    def on_list_view_selected(self, event: ListView.Selected):
        """Handle selection in any list view."""
        if event.list_view.id == "suggestions-list":
            # Handle suggestion selection - join directly
            if hasattr(event.item, 'suggestion_text'):
                suggestion = event.item.suggestion_text
                self._join_channel(suggestion)
    
    def _join_channel(self, channel: str):
        """Join a channel and add it to recent channels."""
        self.recent_channels.add(channel)
        self.post_message(self.ChannelSelected(channel))
        self.dismiss()
    

    
    def add_recent_channel(self, channel: str):
        """Add a channel to recent channels list."""
        self.recent_channels.add(channel)
        # Keep only last 10 recent channels
        if len(self.recent_channels) > 10:
            self.recent_channels = set(list(self.recent_channels)[-10:])
    
    def set_popular_channels(self, channels: List[str]):
        """Update the list of popular channels."""
        self.popular_channels = channels