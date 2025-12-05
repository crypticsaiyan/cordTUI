"""Sidebar widget - channels and servers."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Tree
from textual.message import Message

from src.ui.widgets.user_colors import format_username_colored


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
            self._refresh_tree(select_channel=self.active_channel)
    
    def remove_bookmark(self, channel: str):
        """Remove a channel from bookmarks."""
        if channel in self.bookmarked_channels:
            self.bookmarked_channels.remove(channel)
            self._refresh_tree(select_channel=self.active_channel)
    
    def _refresh_tree(self, select_channel: str = None):
        """Refresh the channel tree display."""
        tree = self.query_one(Tree)
        
        # Use provided select_channel, or fall back to active_channel, or currently selected
        target_channel = select_channel
        if target_channel is None:
            target_channel = self.active_channel
        if target_channel is None and tree.cursor_node and tree.cursor_node.data:
            target_channel = tree.cursor_node.data
        
        # Clear tree by removing all children from root
        tree.clear()
        tree.root.expand()
        
        # Track which line to select
        target_line = None
        line_index = 0
        
        # Add bookmarked channels first with a star
        for channel in self.bookmarked_channels:
            tree.root.add_leaf(f"⭐ {channel}", data=channel)
            if channel == target_channel:
                target_line = line_index
                self.active_channel = channel
            line_index += 1
        
        # Add regular channels (not bookmarked)
        for channel in self.channels:
            if channel not in self.bookmarked_channels:
                tree.root.add_leaf(channel, data=channel)
                if channel == target_channel:
                    target_line = line_index
                    self.active_channel = channel
                line_index += 1
        
        # Move cursor to target channel (line 0 is root, so add 1)
        if target_line is not None:
            tree.cursor_line = target_line + 1
    
    def mark_channel_ready(self, channel: str):
        """Mark a channel as ready (joined successfully)."""
        # This is mainly for visual feedback - could add a checkmark or color
        # For now, just ensure it's in the tree
        pass
    
    def toggle_bookmark(self, channel: str):
        """Toggle bookmark status for a channel."""
        if channel in self.bookmarked_channels:
            self.remove_bookmark(channel)
            return False  # Removed
        else:
            self.add_bookmark(channel)
            return True  # Added
    
    def is_bookmarked(self, channel: str) -> bool:
        """Check if a channel is bookmarked."""
        return channel in self.bookmarked_channels
    
    def select_channel(self, channel: str):
        """Select a channel in the tree by name."""
        tree = self.query_one(Tree)
        for i, node in enumerate(tree.root.children):
            if node.data == channel:
                # Move cursor to this line (line 0 is root, so add 1)
                tree.cursor_line = i + 1
                tree.scroll_to_node(node)
                self.active_channel = channel
                break


class MemberList(Container):
    """Right sidebar with member list."""
    
    can_focus = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.members = []
        self.current_nick = None  # The current user's IRC nick
    
    def compose(self) -> ComposeResult:
        """Compose the member list."""
        with Vertical():
            yield Static("Members (0)", id="member-count")
            yield Static("", id="member-names")
    
    def set_current_nick(self, nick: str):
        """Set the current user's nick for highlighting."""
        self.current_nick = nick
    
    def update_members(self, members: list[str]):
        """Update the member list with current channel members."""
        self.members = sorted(members)
        
        # Update count header
        self.query_one("#member-count", Static).update(f"Members ({len(self.members)})")
        
        # Update names list with colored usernames
        lines = []
        for m in self.members:
            # Strip IRC prefixes for comparison
            clean_name = m.lstrip("@+%~&")
            if self.current_nick and clean_name == self.current_nick:
                lines.append(f"• {format_username_colored(m)} (you)")
            else:
                lines.append(f"• {format_username_colored(m)}")
        names_text = "\n".join(lines)
        self.query_one("#member-names", Static).update(names_text)
    
    def show_loading(self, channel: str):
        """Show loading state for member list."""
        self.query_one("#member-count", Static).update(f"Loading {channel}...")
        self.query_one("#member-names", Static).update("Loading...")
