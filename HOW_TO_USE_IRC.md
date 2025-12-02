# How to Use IRC Chat in Cord-TUI

## Current Status

When you type a message, you see "You: text" because:
1. The IRC connection might be failing
2. You're in "local mode" (messages don't reach the server)
3. The app shows your message locally but it's not being sent

## To Actually Chat with Others on IRC:

### Option 1: Use a Public IRC Server (Easiest)

The default config connects to `irc.libera.chat` which is a real IRC network.

**Steps:**
1. Run the app: `python -m src.main`
2. Watch for connection messages:
   - ✓ "Connected to IRC!" = Working!
   - ✗ "IRC connection failed" = Not working
3. If connected, your messages will reach others in the channel
4. Others on the same channel will see your messages

**To test if it's working:**
- Join a public channel like `#test` or `#python`
- Type a message
- If others respond, it's working!

### Option 2: Test Locally with Two Instances

You can't chat with yourself on IRC, but you can:
1. Open two terminals
2. Run Cord-TUI in both
3. Both connect to the same IRC server
4. Type in one, see it in the other

### Option 3: Check Connection Status

After starting the app, look for these messages:
```
System: Connecting to irc.libera.chat:6667...
System: Joining #general...
System: ✓ Connected to IRC! You can now chat.
```

If you see:
```
System: ✗ IRC connection failed: [error]
System: Running in local mode. Messages won't reach others.
```

Then you're in local mode and messages won't be sent.

## Common Issues:

### 1. Firewall Blocking IRC
**Symptom:** Connection timeout
**Fix:** Allow port 6667 (or 6697 for SSL) in your firewall

### 2. Network Issues
**Symptom:** "Connection refused"
**Fix:** Check your internet connection

### 3. IRC Server Down
**Symptom:** Can't connect
**Fix:** Try a different server in `.cord/config.json`:
```json
{
  "servers": [
    {
      "name": "Libera",
      "host": "irc.libera.chat",
      "port": 6667,
      "ssl": false,
      "nick": "cord_user_123",
      "channels": ["#test"]
    }
  ]
}
```

### 4. Nick Already in Use
**Symptom:** Connection fails with "nick in use"
**Fix:** Change your nick in `.cord/config.json` to something unique

## How IRC Works:

1. **You connect** to an IRC server (like irc.libera.chat)
2. **You join** a channel (like #general)
3. **Everyone in that channel** sees your messages
4. **You see** everyone else's messages in that channel

## Testing the Connection:

### Quick Test:
1. Start Cord-TUI
2. Look for "✓ Connected to IRC!"
3. Type: `Hello, is anyone here?`
4. Wait 10-30 seconds
5. If someone responds, it's working!

### Manual IRC Test (Without Cord-TUI):
```bash
# Install a simple IRC client
sudo apt-get install irssi  # Linux
brew install irssi          # macOS

# Connect
irssi
/connect irc.libera.chat
/join #test
/msg #test Hello from irssi!
```

If this works, then IRC is accessible from your network.

## Current Behavior:

**When IRC is connected:**
- You type: "Hello"
- You see: "You: Hello"
- Others see: "cord_user: Hello"
- Others reply: "alice: Hi there!"
- You see: "alice: Hi there!"

**When IRC is NOT connected (local mode):**
- You type: "Hello"
- You see: "You: Hello"
- You see: "System: (Local only - not connected to IRC)"
- Nobody else sees your message
- You don't see anyone else's messages

## Recommended Channels for Testing:

- `#test` - General testing channel
- `#python` - Python discussion (usually active)
- `#linux` - Linux discussion (usually active)
- `##chat` - General chat (note: two # symbols)

## Advanced: Run Your Own IRC Server

If you want full control:
```bash
# Install ngircd (lightweight IRC server)
sudo apt-get install ngircd

# Start it
sudo systemctl start ngircd

# Connect to localhost
# Edit .cord/config.json:
{
  "servers": [{
    "host": "localhost",
    "port": 6667,
    ...
  }]
}
```

## Debug Mode:

To see what's happening with IRC:
```bash
# Run with Python logging
python -c "import logging; logging.basicConfig(level=logging.DEBUG)" -m src.main
```

## Summary:

**Right now:** You're probably in local mode (not connected)
**To fix:** Check the connection messages when you start the app
**To test:** Join a public channel like #test and see if anyone responds
**If it works:** You'll see messages from others appearing in the chat
