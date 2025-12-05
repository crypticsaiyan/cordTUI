#!/bin/bash
# Verification script for bookmark star updates

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         BOOKMARK STAR UPDATES - VERIFICATION                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if files exist
echo "1. Checking modified files..."
if [ -f "src/ui/widgets/sidebar.py" ]; then
    echo "   ✓ src/ui/widgets/sidebar.py exists"
else
    echo "   ❌ src/ui/widgets/sidebar.py missing"
    exit 1
fi

if [ -f "src/ui/app.py" ]; then
    echo "   ✓ src/ui/app.py exists"
else
    echo "   ❌ src/ui/app.py missing"
    exit 1
fi

# Check for key methods
echo ""
echo "2. Checking for toggle_bookmark method..."
if grep -q "def toggle_bookmark" src/ui/widgets/sidebar.py; then
    echo "   ✓ toggle_bookmark() found"
else
    echo "   ❌ toggle_bookmark() missing"
    exit 1
fi

echo ""
echo "3. Checking for is_bookmarked method..."
if grep -q "def is_bookmarked" src/ui/widgets/sidebar.py; then
    echo "   ✓ is_bookmarked() found"
else
    echo "   ❌ is_bookmarked() missing"
    exit 1
fi

echo ""
echo "4. Checking for selection preservation..."
if grep -q "selected_channel = None" src/ui/widgets/sidebar.py; then
    echo "   ✓ Selection preservation code found"
else
    echo "   ❌ Selection preservation missing"
    exit 1
fi

echo ""
echo "5. Checking for star emoji in tree..."
if grep -q "⭐" src/ui/widgets/sidebar.py; then
    echo "   ✓ Star emoji (⭐) found"
else
    echo "   ❌ Star emoji missing"
    exit 1
fi

echo ""
echo "6. Checking action_toggle_bookmark..."
if grep -q "def action_toggle_bookmark" src/ui/app.py; then
    echo "   ✓ action_toggle_bookmark() found"
else
    echo "   ❌ action_toggle_bookmark() missing"
    exit 1
fi

echo ""
echo "7. Running unit tests..."
source venv/bin/activate
python test_bookmark_stars.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ All tests passed"
else
    echo "   ❌ Tests failed"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         ALL VERIFICATIONS PASSED ✓                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Bookmark star updates are ready to use!"
echo ""
echo "Features:"
echo "  ⭐ Stars appear/disappear when toggling"
echo "  ⭐ Bookmarked channels appear first"
echo "  ⭐ Tree preserves selection"
echo "  ⭐ Ctrl+B keyboard shortcut"
echo "  ⭐ /bookmark and /unbookmark commands"
echo ""
echo "Try it: Press Ctrl+B in the app to toggle bookmarks!"
