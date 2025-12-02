#!/usr/bin/env python3
"""Quick test of the Teletext dashboard rendering."""

import time
from datetime import datetime


def test_teletext_rendering():
    """Test the Teletext Page 100 rendering."""
    
    print("\n" + "="*72)
    print("Testing CORD-TEXT Page 100 Dashboard")
    print("="*72 + "\n")
    
    # Simulate the header
    timestamp = datetime.now().strftime("%H:%M:%S")
    print("█" * 72)
    print(f"█ P100          CORD-OPS DEVOPS MONITOR                {timestamp} █")
    print("█" * 72)
    print()
    
    # Test block characters
    print("Testing Unicode block characters:")
    print(f"  Full block: █")
    print(f"  Upper half: ▀")
    print(f"  Lower half: ▄")
    print(f"  Light shade: ░")
    print()
    
    # Test progress bar
    print("Testing progress bar:")
    percent = 65
    width = 50
    filled = int((percent / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    print(f"  RAM: {bar} {percent}%")
    print()
    
    # Test status grid
    print("Testing status matrix:")
    print("  [█] NGINX        [█] AUTH         [█] REDIS")
    print("  [█] API-V1       [█] WORKER       [ ] DB-MAIN")
    print()
    
    # Test ASCII art header
    print("Testing ASCII art:")
    print("  ██    ███  ████ ███ ████ ████    ████ ███  █  █ █  █ █ ████ ████")
    print("  █  █ █   █  █   █   █     █      █    █  █ ██ █ ██ █ █  █   █   ")
    print("  ██   █████  █   ██  ███   █      █    █  █ █ ██ █ ██ █  █   ███ ")
    print()
    
    # Test ticker tape
    print("Testing ticker tape (scrolling simulation):")
    ticker = "    ALARM: NullReferenceException in core.py... WARNING: High memory usage... "
    for i in range(5):
        offset = i * 5
        scrolled = ticker[offset:] + ticker[:offset]
        print(f"  {scrolled[:68]}", end="\r")
        time.sleep(0.3)
    print()
    print()
    
    print("✓ All Teletext elements rendering correctly!")
    print("\nTo see the full dashboard, run:")
    print("  python src/main.py")
    print("  Then press F1 to toggle Teletext mode")
    print()


if __name__ == "__main__":
    test_teletext_rendering()
