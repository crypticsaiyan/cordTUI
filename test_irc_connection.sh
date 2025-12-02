#!/bin/bash
# Quick IRC connection test script

echo "╔════════════════════════════════════════╗"
echo "║   Cord-TUI IRC Connection Test        ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Test 1: Network connectivity
echo "📡 Test 1: Checking network connectivity..."
if ping -c 1 -W 2 irc.libera.chat &> /dev/null; then
    echo "   ✓ Can reach irc.libera.chat"
else
    echo "   ✗ Cannot reach irc.libera.chat (check internet)"
    exit 1
fi

# Test 2: Port accessibility
echo ""
echo "🔌 Test 2: Checking IRC port (6667)..."
if timeout 3 bash -c "echo > /dev/tcp/irc.libera.chat/6667" 2>/dev/null; then
    echo "   ✓ Port 6667 is accessible"
else
    echo "   ✗ Port 6667 is blocked (firewall?)"
    exit 1
fi

# Test 3: Basic IRC protocol
echo ""
echo "💬 Test 3: Testing IRC protocol..."
RESPONSE=$(timeout 5 bash -c '
    exec 3<>/dev/tcp/irc.libera.chat/6667
    echo "NICK testbot_$$" >&3
    echo "USER testbot 0 * :Test Bot" >&3
    sleep 2
    cat <&3 &
    sleep 1
    kill $! 2>/dev/null
' 2>&1)

if echo "$RESPONSE" | grep -q "NOTICE"; then
    echo "   ✓ IRC server responded correctly"
else
    echo "   ⚠ Unexpected response from server"
fi

# Summary
echo ""
echo "╔════════════════════════════════════════╗"
echo "║   Test Results                         ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "If all tests passed, Cord-TUI should be able to connect!"
echo ""
echo "Next steps:"
echo "1. Run: python -m src.main"
echo "2. Look for: '✓ Connected to IRC!'"
echo "3. Join #test channel"
echo "4. Open another IRC client and join #test"
echo "5. Start chatting!"
echo ""
echo "Recommended test client:"
echo "  Web: https://web.libera.chat/"
echo "  CLI: irssi (install: sudo apt-get install irssi)"
echo ""
