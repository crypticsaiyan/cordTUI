"""Sidebar widget - channels and servers."""

import asyncio
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
    
    class DirectMessageSelected(Message):
        """Message posted when a DM conversation is selected."""
        
        def __init__(self, nick: str):
            super().__init__()
            self.nick = nick
    
    def __init__(self, channels: list[str], bookmarked_channels: list[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.channels = channels
        self.bookmarked_channels = bookmarked_channels or []
        self.active_channel = None
        self.active_dm = None  # Currently selected DM
        self.dm_conversations = []  # List of nicks with active DM conversations
        self.dm_unread = {}  # Track unread DMs: {nick: count}
        self.channel_unread = {}  # Track unread channel messages: {channel: count}
    
    def compose(self) -> ComposeResult:
        """Compose the sidebar."""
        with Vertical():
            yield Static("phosphor", classes="server-name")
            tree = Tree("Navigation")
            tree.root.expand()
            
            # Add DM section
            dm_node = tree.root.add("💬 Direct Messages", data="__dm_section__")
            dm_node.expand()
            for nick in self.dm_conversations:
                unread = self.dm_unread.get(nick, 0)
                label = f"  {nick}" + (f" ({unread})" if unread > 0 else "")
                dm_node.add_leaf(label, data=f"dm:{nick}")
            
            # Add channels section
            channels_node = tree.root.add("# Channels", data="__channels_section__")
            channels_node.expand()
            
            # Add bookmarked channels first with a star
            if self.bookmarked_channels:
                for channel in self.bookmarked_channels:
                    unread = self.channel_unread.get(channel, 0)
                    label = f"⭐ {channel}" + (f" ({unread})" if unread > 0 else "")
                    channels_node.add_leaf(label, data=channel)
            
            # Add regular channels
            for channel in self.channels:
                if channel not in self.bookmarked_channels:
                    unread = self.channel_unread.get(channel, 0)
                    label = f"  {channel}" + (f" ({unread})" if unread > 0 else "")
                    channels_node.add_leaf(label, data=channel)
            
            yield tree
    
    def on_tree_node_selected(self, event: Tree.NodeSelected):
        """Handle channel or DM selection."""
        if event.node.data:
            data = event.node.data
            # Skip section headers
            if data in ("__dm_section__", "__channels_section__"):
                return
            
            # Handle DM selection
            if data.startswith("dm:"):
                nick = data[3:]  # Remove "dm:" prefix
                self.active_dm = nick
                self.active_channel = None
                # Clear unread count
                self.dm_unread[nick] = 0
                self.post_message(self.DirectMessageSelected(nick))
            else:
                # Handle channel selection
                self.active_channel = data
                self.active_dm = None
                # Clear unread count for channel
                self.channel_unread[data] = 0
                self._refresh_tree(select_channel=data)
                self.post_message(self.ChannelSelected(data))
    
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
    
    def _refresh_tree(self, select_channel: str = None, select_dm: str = None):
        """Refresh the channel tree display."""
        tree = self.query_one(Tree)
        
        # Use provided select_channel/dm, or fall back to active ones
        target_channel = select_channel or self.active_channel
        target_dm = select_dm or self.active_dm
        
        # Clear tree by removing all children from root
        tree.clear()
        tree.root.expand()
        
        # Track which line to select
        target_line = None
        line_index = 0
        
        # Add DM section
        dm_node = tree.root.add("💬 Direct Messages", data="__dm_section__")
        dm_node.expand()
        line_index += 1
        
        for nick in self.dm_conversations:
            unread = self.dm_unread.get(nick, 0)
            label = f"  {nick}" + (f" ({unread})" if unread > 0 else "")
            dm_node.add_leaf(label, data=f"dm:{nick}")
            if nick == target_dm:
                target_line = line_index
                self.active_dm = nick
            line_index += 1
        
        # Add channels section
        channels_node = tree.root.add("# Channels", data="__channels_section__")
        channels_node.expand()
        line_index += 1
        
        # Add bookmarked channels first with a star
        for channel in self.bookmarked_channels:
            unread = self.channel_unread.get(channel, 0)
            label = f"⭐ {channel}" + (f" ({unread})" if unread > 0 else "")
            channels_node.add_leaf(label, data=channel)
            if channel == target_channel:
                target_line = line_index
                self.active_channel = channel
            line_index += 1
        
        # Add regular channels (not bookmarked)
        for channel in self.channels:
            if channel not in self.bookmarked_channels:
                unread = self.channel_unread.get(channel, 0)
                label = f"  {channel}" + (f" ({unread})" if unread > 0 else "")
                channels_node.add_leaf(label, data=channel)
                if channel == target_channel:
                    target_line = line_index
                    self.active_channel = channel
                line_index += 1
        
        # Move cursor to target (line 0 is root, so add 1)
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
        self._refresh_tree(select_channel=channel)
    
    def add_dm_conversation(self, nick: str):
        """Add a DM conversation to the sidebar."""
        if nick not in self.dm_conversations:
            self.dm_conversations.insert(0, nick)  # Add to top
            self._refresh_tree()
    
    def remove_dm_conversation(self, nick: str):
        """Remove a DM conversation from the sidebar."""
        if nick in self.dm_conversations:
            self.dm_conversations.remove(nick)
            if nick in self.dm_unread:
                del self.dm_unread[nick]
            self._refresh_tree()
    
    def increment_dm_unread(self, nick: str):
        """Increment unread count for a DM conversation."""
        if nick not in self.dm_conversations:
            self.dm_conversations.insert(0, nick)
        self.dm_unread[nick] = self.dm_unread.get(nick, 0) + 1
        self._refresh_tree()
    
    def clear_dm_unread(self, nick: str):
        """Clear unread count for a DM conversation."""
        self.dm_unread[nick] = 0
        self._refresh_tree()
    
    def select_dm(self, nick: str):
        """Select a DM conversation in the tree."""
        if nick not in self.dm_conversations:
            self.dm_conversations.insert(0, nick)
        self.active_dm = nick
        self.active_channel = None
        self.dm_unread[nick] = 0
        self._refresh_tree(select_dm=nick)
    
    def increment_channel_unread(self, channel: str):
        """Increment unread count for a channel."""
        self.channel_unread[channel] = self.channel_unread.get(channel, 0) + 1
        self._refresh_tree()
    
    def clear_channel_unread(self, channel: str):
        """Clear unread count for a channel."""
        self.channel_unread[channel] = 0
        self._refresh_tree()


class MemberList(Container):
    """Right sidebar with member list."""
    
    can_focus = True
    
    class MemberClicked(Message):
        """Message posted when a member is clicked for DM."""
        
        def __init__(self, nick: str):
            super().__init__()
            self.nick = nick
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.members = []
        self.current_nick = None  # The current user's IRC nick
        self.selected_index = 0  # For keyboard navigation
        self._skull_animation_task = None
        self._skull_frame = 0
    
    def compose(self) -> ComposeResult:
        """Compose the member list."""
        with Vertical():
            yield Static("Members (0)", id="member-count")
            yield Static("[dim]Click or Enter to DM[/]", id="member-hint")
            tree = Tree("Users")
            tree.root.expand()
            yield tree
    
    def set_current_nick(self, nick: str):
        """Set the current user's nick for highlighting."""
        self.current_nick = nick
    
    def on_tree_node_selected(self, event: Tree.NodeSelected):
        """Handle member selection for DM."""
        if event.node.data:
            nick = event.node.data
            # Don't DM yourself
            if nick != self.current_nick:
                self.post_message(self.MemberClicked(nick))
    
    def show_loading(self, channel: str):
        """Show loading state for member list."""
        # Check if Halloween theme is active
        is_halloween = hasattr(self.app, 'active_theme') and self.app.active_theme == "halloween"
        
        if is_halloween:
            self.query_one("#member-count", Static).update(f"💀 Loading {channel}...")
            loading_text = "💀 ☠️ 💀"
        else:
            self.query_one("#member-count", Static).update(f"Loading {channel}...")
            loading_text = "Loading..."
        
        tree = self.query_one(Tree)
        tree.clear()
        tree.root.expand()
        tree.root.add_leaf(loading_text, data=None)
        
        # Start animated loading if Halloween
        if is_halloween:
            self._start_skull_animation()

    def _start_skull_animation(self):
        """Start the rotating skull animation."""
        # Cancel any existing animation
        if self._skull_animation_task:
            self._skull_animation_task.cancel()
        self._skull_frame = 0
        self._skull_animation_task = asyncio.create_task(self._animate_skulls())
    
    def _stop_skull_animation(self):
        """Stop the skull animation."""
        if self._skull_animation_task:
            self._skull_animation_task.cancel()
            self._skull_animation_task = None
    
    async def _animate_skulls(self):
        """Animate rotating skulls in the loading indicator."""
        skull_frames = [
            "💀 ☠️ 💀",
            "☠️ 💀 ☠️",
            "💀 👻 💀",
            "👻 💀 👻",
            "💀 🎃 💀",
            "🎃 💀 🎃",
            "💀 🦇 💀",
            "🦇 💀 🦇",
        ]
        
        try:
            while True:
                tree = self.query_one(Tree)
                # Only animate if tree has the loading leaf
                if tree.root.children:
                    first_child = tree.root.children[0]
                    if first_child.data is None:  # Loading indicator
                        frame = skull_frames[self._skull_frame % len(skull_frames)]
                        first_child.set_label(frame)
                        self._skull_frame += 1
                
                await asyncio.sleep(0.3)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
    
    def update_members(self, members: list[str]):
        """Update the member list with current channel members."""
        # Stop any skull animation when members load
        self._stop_skull_animation()
        
        self.members = sorted(members)
        
        # Update count header
        is_halloween = hasattr(self.app, 'active_theme') and self.app.active_theme == "halloween"
        if is_halloween:
            self.query_one("#member-count", Static).update(f"🎃 Members ({len(self.members)})")
        else:
            self.query_one("#member-count", Static).update(f"Members ({len(self.members)})")
        
        # Update tree with members
        tree = self.query_one(Tree)
        tree.clear()
        tree.root.expand()
        
        for m in self.members:
            # Strip IRC prefixes for comparison
            clean_name = m.lstrip("@+%~&")
            if self.current_nick and clean_name == self.current_nick:
                label = f"{format_username_colored(m)} (you)"
            else:
                label = format_username_colored(m)
            tree.root.add_leaf(label, data=clean_name)
