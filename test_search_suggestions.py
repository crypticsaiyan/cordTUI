#!/usr/bin/env python3
"""Test the enhanced channel search with suggestions."""

import asyncio
from textual.app import App
from src.ui.widgets.channel_search import ChannelSearchScreen


class TestSearchApp(App):
    """Simple app to test the search functionality."""
    
    def __init__(self):
        super().__init__()
        self.channels = [
            {'name': '#python', 'users': 150, 'topic': 'Python programming discussion'},
            {'name': '#javascript', 'users': 120, 'topic': 'JavaScript and web development'},
            {'name': '#linux', 'users': 200, 'topic': 'Linux support and discussion'},
            {'name': '#programming', 'users': 300, 'topic': 'General programming chat'},
            {'name': '#help', 'users': 80, 'topic': 'Get help with various topics'},
            {'name': '#python-dev', 'users': 45, 'topic': 'Python development discussions'},
            {'name': '#python-help', 'users': 60, 'topic': 'Python help and support'},
            {'name': '#general', 'users': 250, 'topic': 'General discussion'},
            {'name': '#random', 'users': 180, 'topic': 'Random chat and off-topic'},
            {'name': '#gaming', 'users': 90, 'topic': 'Gaming discussion'},
        ]
    
    def on_mount(self):
        """Show the search screen immediately."""
        search_screen = ChannelSearchScreen()
        # Simulate having some recent channels
        search_screen.recent_channels.update(['#mychannel', '#work', '#friends'])
        self.push_screen(search_screen)
    
    def request_channel_list(self, pattern=None):
        """Mock channel list request."""
        # Simulate receiving channel list
        if hasattr(self.screen, 'update_channel_list'):
            self.screen.update_channel_list(self.channels)
    
    def on_channel_search_screen_channel_selected(self, event):
        """Handle channel selection."""
        print(f"Selected channel: {event.channel}")
        self.exit()


if __name__ == "__main__":
    app = TestSearchApp()
    app.run()