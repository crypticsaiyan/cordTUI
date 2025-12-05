"""User color assignment for consistent username coloring."""

# Color palette for usernames - distinct, readable Rich colors
USER_COLORS = [
    "#00ffff",  # cyan
    "#ff00ff",  # magenta
    "#00ff00",  # green
    "#ffff00",  # yellow
    "#5865f2",  # blue
    "#ff6b6b",  # soft red
    "#43b581",  # emerald green
    "#faa61a",  # orange
    "#e91e63",  # pink
    "#9b59b6",  # purple
    "#1abc9c",  # teal
    "#3498db",  # light blue
    "#e67e22",  # orange
    "#2ecc71",  # emerald
    "#f1c40f",  # gold
    "#e74c3c",  # red
]


def get_user_color(username: str) -> str:
    """Get a consistent color for a username based on hash.
    
    The same username will always get the same color.
    """
    # Strip IRC prefixes like @ (op) and + (voice)
    clean_name = username.lstrip("@+%~&")
    
    # Use hash to get consistent color assignment
    color_index = hash(clean_name) % len(USER_COLORS)
    return USER_COLORS[color_index]


def format_username_colored(username: str) -> str:
    """Format a username with its assigned color for Rich markup."""
    color = get_user_color(username)
    return f"[{color}]{username}[/]"
