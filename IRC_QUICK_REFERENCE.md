# IRC Quick Reference Card

## 🚀 Getting Started

```bash
# 1. Start Cord-TUI
python -m src.main

# 2. Wait for connection message
# "✓ Connected to IRC! You can now chat."

# 3. Start chatting!
```

## 💬 Basic Usage

| Action | How To |
|--------|--------|
| Send message | Type and press Enter |
| Switch channel | Click channel in left sidebar |
| View members | Check right sidebar |
| See member count | Top of right sidebar |

## 🌐 Default Setup

**Server**: Libera.Chat (irc.libera.chat)  
**Channels**: #python, #linux, #programming  
**Your nick**: cord_user (change in config)

## ⚙️ Quick Config

Edit `.cord/config.json`:

```json
{
  "servers": [{
    "host": "irc.libera.chat",
    "port": 6667,
    "nick": "your_nickname",
    "channels": ["#python", "#linux"]
  }]
}
```

## 🎯 Popular Channels

### Libera.Chat
- `#python` - Python programming
- `#linux` - Linux help
- `#programming` - General coding
- `#git` - Git version control
- `#vim` - Vim editor
- `#bash` - Bash scripting
- `#javascript` - JavaScript
- `#rust` - Rust language

## 🔧 IRC Commands

Type these in the chat input:

| Command | Description |
|---------|-------------|
| `/join #channel` | Join a channel |
| `/part #channel` | Leave a channel |
| `/nick newnick` | Change nickname |
| `/msg user text` | Private message |
| `/quit` | Disconnect |

## 🐛 Quick Troubleshooting

**Not connected?**
- Check internet connection
- Verify server in config.json
- Look for error messages in chat

**Nickname in use?**
- Change nick in .cord/config.json
- Make it unique

**No messages?**
- Some channels are quiet
- Try #python (usually active)
- Wait a few minutes

**Member list empty?**
- Wait 5-10 seconds after joining
- Check if you're in the channel

## 🧪 Test Connection

```bash
python test_public_irc.py
```

Should show:
- ✅ Connected
- 📡 Joining #python
- 👥 Member list
- 📨 Messages (if any)

## 📚 More Help

- Full guide: [PUBLIC_IRC_GUIDE.md](PUBLIC_IRC_GUIDE.md)
- Troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- IRC basics: https://www.irchelp.org/

## 💡 Pro Tips

1. **Be patient** - IRC is slower than Discord
2. **Read the topic** - Type `/topic` to see channel rules
3. **Don't spam** - Wait for responses
4. **Use pastebin** - For code longer than 3 lines
5. **Be respectful** - IRC has been around since 1988!

---

**Happy chatting!** 🎉
