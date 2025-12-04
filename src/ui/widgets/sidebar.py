"""Sidebar widget - channels and servers."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Tree, ListView, ListItem, Label
from textual.reactive import reactive
from textual.message import Message


class Sidebar(Container):
    """Left sidebar with channel list."""
    
    class ChannelSelected(Message):
        """Message posted when a channel is selected."""
        
        def __init__(self, channel: str):
            super().__init__()
            self.channel = channel
    
    def __init__(self, channels: list[str], bookmarked_channels: list[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.channels = channels
        self.bookmarked_channels = bookmarked_channels or []
        self.active_channel = None
    
    def compose(self) -> ComposeResult:
        """Compose the sidebar."""
        with Vertical():
            yield Static("CORD-TUI", classes="server-name")
            tree = Tree("Channels")
            tree.root.expand()
            
            # Add bookmarked channels first with a star
            if self.bookmarked_channels:
                for channel in self.bookmarked_channels:
                    tree.root.add_leaf(f"⭐ {channel}", data=channel)
            
            # Add regular channels
            for channel in self.channels:
                if channel not in self.bookmarked_channels:
                    tree.root.add_leaf(channel, data=channel)
            
            yield tree
    
    def on_tree_node_selected(self, event: Tree.NodeSelected):
        """Handle channel selection."""
        if event.node.data:
            self.active_channel = event.node.data
            self.post_message(self.ChannelSelected(event.node.data))
    
    def update_channels(self, channels: list[str]):
        """Update the channel list with new channels."""
        self.channels = channels
        self._refresh_tree()
    
    def add_bookmark(self, channel: str):
        """Add a channel to bookmarks."""
        if channel not in self.bookmarked_channels:
            self.bookmarked_channels.append(channel)
            self._refresh_tree()
    
    def remove_bookmark(self, channel: str):
        """Remove a channel from bookmarks."""
        if channel in self.bookmarked_channels:
            self.bookmarked_channels.remove(channel)
            self._refresh_tree()
    
    def _refresh_tree(self):
        """Refresh the channel tree display."""
        tree = self.query_one(Tree)
        tree.root.remove_children()
        
        # Add bookmarked channels first with a star
        if self.bookmarked_channels:
            for channel in self.bookmarked_channels:
                tree.root.add_leaf(f"⭐ {channel}", data=channel)
        
        # Add regular channels
        for channel in self.channels:
            if channel not in self.bookmarked_channels:
                tree.root.add_leaf(channel, data=channel)


class MemberList(Container):
    """Right sidebar with member list."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.members = []
        self.member_list_view = None
    
    def compose(self) -> ComposeResult:
        """Compose the member list."""
        with Vertical():
            yield Static("Members (0)", classes="member-header", id="member-count")
            self.member_list_view = ListView(id="member-list-view")
            yield self.member_list_view
    
    def update_members(self, members: list[str]):
        """Update the member list with current channel members."""
        self.members = sorted(members)
        
        # Update count header
        count_widget = self.query_one("#member-count", Static)
        count_widget.update(f"Members ({len(self.members)})")
        
        # Clear and rebuild list
        if self.member_list_view:
            self.member_list_view.clear()
            for member in self.members:
                item = ListItem(Label(f"• {member}", classes="member-online"))
                self.member_list_view.append(item)
    
    def show_loading(self, channel: str):
        """Show loading state for member list."""
        count_widget = self.query_one("#member-count", Static)
        count_widget.update(f"Loading {channel}...")
        
        if self.member_list_view:
            self.member_list_view.clear()
            item = ListItem(Label("Loading members...", classes="member-loading"))
            self.member_list_view.append(item)
