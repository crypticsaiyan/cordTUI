"""Command palette widget for slash command suggestions."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, OptionList
from textual.widgets.option_list import Option
from textual.message import Message


# Available commands with descriptions
COMMANDS = [
    ("/join", "Join or search for a channel"),
    ("/bookmark", "Bookmark current or specified channel"),
    ("/unbookmark", "Remove bookmark from channel"),
    ("/bookmarks", "List all bookmarked channels"),
    ("/send", "Send a file via Magic Wormhole"),
    ("/grab", "Receive a file via Magic Wormhole"),
    ("/ai", "Ask AI assistant (use 'private' prefix for private response)"),
]


class CommandPalette(Static):
    """A popup showing available slash commands."""

    DEFAULT_CSS = """
    CommandPalette {
        layer: overlay;
        width: 50;
        height: auto;
        max-height: 12;
        background: $surface;
        border: solid $primary;
        padding: 0 1;
        display: none;
    }

    CommandPalette.visible {
        display: block;
    }

    CommandPalette .command-item {
        padding: 0 1;
    }

    CommandPalette .command-item.highlighted {
        background: $accent;
        color: $text;
    }

    CommandPalette .command-name {
        color: $success;
    }

    CommandPalette .command-desc {
        color: $text-muted;
    }
    """

    class CommandSelected(Message):
        """Posted when a command is selected."""

        def __init__(self, command: str):
            super().__init__()
            self.command = command

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.highlighted_index = 0
        self.filtered_commands = COMMANDS.copy()

    def compose(self) -> ComposeResult:
        """Compose the command palette."""
        yield Vertical(id="command-list")

    def on_mount(self):
        """Build the initial command list."""
        self._rebuild_list()

    def _rebuild_list(self):
        """Rebuild the command list display."""
        container = self.query_one("#command-list", Vertical)
        container.remove_children()

        for i, (cmd, desc) in enumerate(self.filtered_commands):
            if i == self.highlighted_index:
                # Highlighted item - bright colors with background
                item = Static(
                    f"[bold white on #5865F2] {cmd} [/]  [white]{desc}[/]",
                    classes="command-item highlighted",
                )
            else:
                # Normal item
                item = Static(
                    f"[bold #43b581]{cmd}[/]  [#8e9297]{desc}[/]",
                    classes="command-item",
                )
            container.mount(item)

    def show(self):
        """Show the command palette."""
        self.add_class("visible")
        self.highlighted_index = 0
        self.filtered_commands = COMMANDS.copy()
        self._rebuild_list()

    def hide(self):
        """Hide the command palette."""
        self.remove_class("visible")

    def is_visible(self) -> bool:
        """Check if palette is visible."""
        return self.has_class("visible")

    def filter(self, text: str):
        """Filter commands based on input text."""
        # Remove leading slash for matching
        search = text.lstrip("/").lower()

        if not search:
            self.filtered_commands = COMMANDS.copy()
        else:
            self.filtered_commands = [
                (cmd, desc)
                for cmd, desc in COMMANDS
                if search in cmd.lower() or search in desc.lower()
            ]

        # Reset highlight if out of bounds
        if self.highlighted_index >= len(self.filtered_commands):
            self.highlighted_index = max(0, len(self.filtered_commands) - 1)

        self._rebuild_list()

    def move_up(self):
        """Move highlight up."""
        if self.filtered_commands:
            self.highlighted_index = (self.highlighted_index - 1) % len(self.filtered_commands)
            self._rebuild_list()

    def move_down(self):
        """Move highlight down."""
        if self.filtered_commands:
            self.highlighted_index = (self.highlighted_index + 1) % len(self.filtered_commands)
            self._rebuild_list()

    def select_current(self) -> str | None:
        """Select the currently highlighted command."""
        if self.filtered_commands:
            cmd, _ = self.filtered_commands[self.highlighted_index]
            return cmd
        return None
