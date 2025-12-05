# Channel Bookmarks Feature

## Overview
Bookmark your favorite channels so they persist across app restarts and appear at the top of the sidebar with a star (⭐).

## Commands

### `/bookmark [#channel]`
Bookmark the current channel or a specified channel.
- **Example 1:** `/bookmark` - Bookmarks the current channel
- **Example 2:** `/bookmark #python` - Bookmarks #python channel

### `/unbookmark [#channel]`
Remove bookmark from the current channel or a specified channel.
- **Example 1:** `/unbookmark` - Removes bookmark from current channel
- **Example 2:** `/unbookmark #python` - Removes bookmark from #python

### `/bookmarks`
List all bookmarked channels.

## Keybind

**Ctrl+B** - Toggle bookmark for the current channel
- Press once to bookmark
- Press again to unbookmark
- Works instantly without typing commands

## Features

✅ **Persistent Storage** - Bookmarks are saved to `.cord/bookmarks.json` and persist across app restarts

✅ **Visual Indicator** - Bookmarked channels show with ⭐ in the sidebar

✅ **Priority Display** - Bookmarked channels appear at the top of the channel list

✅ **Quick Toggle** - Use Ctrl+B to instantly bookmark/unbookmark the current channel

## Usage Example

```
# Bookmark your favorite channels
/bookmark #python
/bookmark #javascript
/bookmark #rust

# Or use the keybind
[Switch to #golang]
[Press Ctrl+B]  # Bookmarks #golang

# List all bookmarks
/bookmarks

# Remove a bookmark
/unbookmark #javascript
```

## Storage Location

Bookmarks are stored in: `.cord/bookmarks.json`

Example file structure:
```json
{
  "channels": [
    "#python",
    "#rust",
    "#golang"
  ]
}
```

## Tips

- Bookmark channels you visit frequently for quick access
- Bookmarked channels stay in the sidebar even after closing the app
- You can bookmark channels before joining them
- Use Ctrl+B for the fastest bookmark toggle
