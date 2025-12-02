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
    
    def __init__(self, channels: list[str], **kwargs):
        super().__init__(**kwargs)
        self.channels = channels
        self.active_channel = None
    
    def compose(self) -> ComposeResult:
        """Compose the sidebar."""
        with Vertical():
            yield Static("📡 CORD-TUI", classes="server-name")
            tree = Tree("Channels")
            tree.root.expand()
            for channel in self.channels:
                tree.root.add_leaf(f"# {channel}", data=channel)
            yield tree
    
    def on_tree_node_selected(self, event: Tree.NodeSelected):
        """Handle channel selection."""
        if event.node.data:
            self.active_channel = event.node.data
            self.post_message(self.ChannelSelected(event.node.data))


class MemberList(Container):
    """Right sidebar with member list."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.members = []
    
    def compose(self) -> ComposeResult:
        """Compose the member list."""
        with Vertical():
            yield Static("👥 Members", classes="member-header")
            yield ListView(
                ListItem(Label("● alice", classes="member-online")),
                ListItem(Label("● bob", classes="member-online")),
                ListItem(Label("○ charlie", classes="member-offline")),
            )
    
    def update_members(self, online: list[str], offline: list[str]):
        """Update the member list."""
        # TODO: Implement dynamic member updates
        pass
