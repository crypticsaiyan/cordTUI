# Testing Cord-TUI with Two Clients

## Method 1: Two Cord-TUI Instances (Recommended)

### Step 1: Open Two Terminals

**Terminal 1:**
```bash
cd /home/cryptosaiyan/Documents/irc-tui
source venv/bin/activate
python -m src.main
```

**Terminal 2:**
```bash
cd /home/cryptosaiyan/Documents/irc-tui
source venv/bin/activate
python -m src.main
```

### Step 2: Change Nick for Second Instance

Before running the second instance, edit the config to use a different nickname:

```bash
# In Terminal 2, before running:
cp .cord/config.json .cord/config2.json
```

Edit `.cord/config2.json`:
```json
{
  "servers": [
    {
      "name": "Default",
      "host": "irc.libera.chat",
      "port": 6667,
      "ssl": false,
      "nick": "cord_user2",  // Changed from cord_user
      "channels": ["#test"]   // Use #test for testing
    }
  ],
  ...
}
```

Then run with the alternate config:
```bash
# We need to modify the app to accept config path
# For now, just edit .cord/config.json directly before each run
```

### Step 3: Test Communication

1. **In Terminal 1:** Type "Hello from client 1"
2. **In Terminal 2:** You should see "cord_user: Hello from client 1"
3. **In Terminal 2:** Type "Hi from client 2"
4. **In Terminal 1:** You should see "cord_user2: Hi from client 2"

---

## Method 2: Cord-TUI + Standard IRC Client (Easier)

This is actually easier because you don't need to change configs!

### Step 1: Install a Simple IRC Client

**Option A: irssi (Terminal-based)**
```bash
sudo apt-get install irssi
```

**Option B: HexChat (GUI)**
```bash
sudo apt-get install hexchat
```

**Option C: weechat (Terminal-based)**
```bash
sudo apt-get install weechat
```

### Step 2: Run Cord-TUI in Terminal 1

```bash
cd /home/cryptosaiyan/Documents/irc-tui
source venv/bin/activate
python -m src.main
```

Watch for: "✓ Connected to IRC!"

### Step 3: Connect with Standard IRC Client in Terminal 2

**Using irssi:**
```bash
irssi

# In irssi, type these commands:
/connect irc.libera.chat
/nick testuser123
/join #test
/msg #test Hello from irssi!
```

**Using weechat:**
```bash
weechat

# In weechat:
/server add libera irc.libera.chat/6667
/connect libera
/nick testuser123
/join #test
Hello from weechat!
```

**Using HexChat (GUI):**
1. Open HexChat
2. Add network: Libera.Chat
3. Connect
4. Join channel: #test
5. Type your message

### Step 4: Test Communication

1. **In Cord-TUI:** Type "Hello from Cord-TUI"
2. **In irssi/weechat/HexChat:** You should see "cord_user: Hello from Cord-TUI"
3. **In irssi/weechat/HexChat:** Type "Hi back!"
4. **In Cord-TUI:** You should see "testuser123: Hi back!"

---

## Method 3: Quick Test with Web IRC Client (Fastest!)

### Step 1: Run Cord-TUI
```bash
python -m src.main
```

### Step 2: Open Web IRC Client

Go to: https://web.libera.chat/

1. Enter nickname: "webtester"
2. Channel: #test
3. Click "Start"

### Step 3: Chat!

- Type in Cord-TUI: "Hello from terminal"
- Type in web client: "Hello from web"
- You should see each other's messages!

---

## Troubleshooting

### Issue: "Nick already in use"

**Solution:** Change your nick in `.cord/config.json`:
```json
"nick": "cord_user_RANDOM123"
```

### Issue: "Cannot connect"

**Check:**
```bash
# Test if IRC port is accessible
telnet irc.libera.chat 6667

# If this works, you'll see:
# Connected to irc.libera.chat
```

### Issue: Messages not appearing

**Check in Cord-TUI:**
- Look for "✓ Connected to IRC!" message
- If you see "✗ IRC connection failed", it's not working

**Debug:**
```bash
# Run with more verbose output
python -m src.main 2>&1 | tee debug.log
```

---

## Quick Test Script

Let me create a test script for you:

Save this as `test_irc.sh`:
```bash
#!/bin/bash

echo "=== IRC Connection Test ==="
echo ""
echo "Testing connection to irc.libera.chat..."
echo ""

# Test 1: Can we reach the server?
if timeout 5 bash -c "echo > /dev/tcp/irc.libera.chat/6667" 2>/dev/null; then
    echo "✓ IRC server is reachable"
else
    echo "✗ Cannot reach IRC server (firewall/network issue)"
    exit 1
fi

# Test 2: Try to connect with netcat
echo ""
echo "Attempting basic IRC connection..."
(
    echo "NICK testbot123"
    echo "USER testbot 0 * :Test Bot"
    sleep 2
    echo "JOIN #test"
    echo "PRIVMSG #test :Test message from script"
    sleep 2
    echo "QUIT"
) | nc irc.libera.chat 6667

echo ""
echo "If you saw IRC protocol messages above, the server is working!"
```

Run it:
```bash
chmod +x test_irc.sh
./test_irc.sh
```

---

## Recommended Test Procedure

### 1. First, verify IRC works at all:
```bash
# Install netcat if needed
sudo apt-get install netcat

# Quick test
echo -e "NICK testbot\nUSER testbot 0 * :Test\nJOIN #test\nPRIVMSG #test :Hello\nQUIT" | nc irc.libera.chat 6667
```

### 2. Then test Cord-TUI:
```bash
python -m src.main
# Watch for connection messages
```

### 3. Finally, test with second client:
```bash
# In another terminal
irssi
/connect irc.libera.chat
/join #test
```

---

## Expected Behavior

### When Working:
```
Terminal 1 (Cord-TUI):
> You: Hello everyone
> testuser: Hi there!
> testuser: How are you?

Terminal 2 (irssi):
<cord_user> Hello everyone
> Hi there!
> How are you?
```

### When NOT Working:
```
Terminal 1 (Cord-TUI):
> You: Hello everyone
> System: (Local only - not connected to IRC)

Terminal 2 (irssi):
[Nothing appears]
```

---

## Pro Tip: Use tmux for Split Screen

```bash
# Install tmux
sudo apt-get install tmux

# Start tmux
tmux

# Split screen vertically
Ctrl+b then %

# Switch between panes
Ctrl+b then arrow keys

# Now run Cord-TUI in left pane, irssi in right pane
# You can see both at once!
```

---

## Summary

**Easiest method:** 
1. Run Cord-TUI
2. Open https://web.libera.chat/ in browser
3. Join same channel (#test)
4. Chat!

**Best for testing:**
1. Terminal 1: Cord-TUI
2. Terminal 2: irssi
3. Both join #test
4. Type in both, see messages in both

**If nothing works:**
- Check the connection messages in Cord-TUI
- Try the test script above
- Check firewall/network settings
