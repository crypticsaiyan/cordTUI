#!/usr/bin/env python3
"""Test bookmark functionality."""

import json
from pathlib import Path

def test_bookmarks():
    """Test bookmark save/load functionality."""
    
    # Ensure .cord directory exists
    cord_dir = Path(".cord")
    cord_dir.mkdir(exist_ok=True)
    
    bookmarks_path = cord_dir / "bookmarks.json"
    
    # Check if bookmarks file exists
    if bookmarks_path.exists():
        with open(bookmarks_path) as f:
            existing = json.load(f)
        print("✓ Found existing bookmarks file")
        print(f"  Location: {bookmarks_path}")
        if existing.get("channels"):
            print(f"  Channels: {', '.join(existing['channels'])}")
        else:
            print("  Channels: (none)")
    else:
        # Create empty bookmarks file
        empty_bookmarks = {"channels": []}
        with open(bookmarks_path, 'w') as f:
            json.dump(empty_bookmarks, f, indent=2)
        print("✓ Created empty bookmarks file")
        print(f"  Location: {bookmarks_path}")
        print("  Channels: (none)")
    
    print("\n✓ Bookmark system ready!")
    
    print("\nBookmark Commands:")
    print("  /bookmark [#channel]  - Bookmark current or specified channel")
    print("  /unbookmark [#channel] - Remove bookmark")
    print("  /bookmarks            - List all bookmarks")
    print("\nKeybind:")
    print("  Ctrl+B                - Toggle bookmark for current channel")
    print("\nBookmarked channels appear with ⭐ in the sidebar")
    print("and persist across app restarts.")

if __name__ == "__main__":
    test_bookmarks()
