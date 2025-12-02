# Public IRC Server Guide

Cord-TUI now supports connecting to public IRC servers like Libera.Chat, allowing you to join real IRC channels and chat with users worldwide.

## 🌐 Default Configuration

By default, Cord-TUI connects to **Libera.Chat** (irc.libera.chat), one of the largest and most popular IRC networks. The default channels are:

- **#python** - Python programming discussion
- **#linux** - Linux help and discussion  
- **#programming** - General programming topics

## 🎯 Features

### Real-time Chat
- Send and receive messages from real IRC users
- Full IRC protocol support
- Automatic reconnection handling

### Live Member Lists
- See who's in each channel in real-time
- Member count displayed in the sidebar
- Updates when users join/leave

### Channel Switching
- Click channels in the left sidebar to switch
- Member list updates automatically
- Input bar shows current channel

## ⚙️ Configuration

Edit `.cord/config.json` to customize your IRC connection:

```json
{
  "servers": [
    {
      "name": "Libera.Chat",
      "host": "irc.libera.chat",
      "port": 6667,
      "ssl": false,
      "nick": "your_nickname",
      "channels": ["#python", "#linux", "#programming"]
    }
  ]
}
```

### Configuration Options

- **name**: Display name for the server
- **host**: IRC server hostname
- **port**: Server port (6667 for plain, 6697 for SSL)
- **ssl**: Enable SSL/TLS encryption (recommended for public servers)
- **nick**: Your IRC nickname (must be unique)
- **channels**: List of channels to auto-join

## 🔒 Using SSL

For secure connections, use SSL:

```json
{
  "host": "irc.libera.chat",
  "port": 6697,
  "ssl": true
}
```

## 🌍 Other Popular IRC Networks

### Libera.Chat (Default)
- **Host**: irc.libera.chat
- **Ports**: 6667 (plain), 6697 (SSL)
- **Focus**: FOSS projects, programming
- **Popular channels**: #python, #linux, #git, #vim

### OFTC
- **Host**: irc.oftc.net
- **Ports**: 6667 (plain), 6697 (SSL)
- **Focus**: Open source projects
- **Popular channels**: #debian, #tor, #llvm

### EFnet
- **Host**: irc.efnet.org
- **Ports**: 6667 (plain), 6697 (SSL)
- **Focus**: General chat, oldest network
- **Popular channels**: #chat, #help

### Rizon
- **Host**: irc.rizon.net
- **Ports**: 6667 (plain), 6697 (SSL)
- **Focus**: Anime, gaming, general
- **Popular channels**: #news, #chat

## 🧪 Testing Connection

Test your IRC connection without launching the full UI:

```bash
python test_public_irc.py
```

This will:
1. Connect to Libera.Chat
2. Join #python
3. Display member list
4. Listen for messages
5. Send a test message
6. Disconnect

## 💡 Tips

### Choosing a Nickname
- Must be unique on the network
- 1-16 characters
- Letters, numbers, and some special chars
- Avoid spaces

### Channel Etiquette
- Read channel topic before posting
- Don't spam or flood
- Be respectful
- Many channels have bots - don't abuse them

### Finding Channels
Once connected, you can:
- Use `/list` command to see all channels (may be rate-limited)
- Check network website for channel directory
- Ask in #help channels

## 🐛 Troubleshooting

### "Nickname already in use"
Change your nick in `.cord/config.json` to something unique.

### "Cannot connect"
- Check your internet connection
- Verify server hostname and port
- Try with SSL disabled first
- Some networks require registration

### "No messages appearing"
- Some channels are quiet - try #python or #linux
- Check if you're actually connected (look for system messages)
- Try sending a message first

### "Member list empty"
- Wait a few seconds after joining
- Some channels hide member lists
- Check if you successfully joined the channel

## 🎮 IRC Commands

While in Cord-TUI, you can use standard IRC commands:

- `/join #channel` - Join a new channel
- `/part #channel` - Leave a channel  
- `/nick newnick` - Change nickname
- `/msg user message` - Private message
- `/quit` - Disconnect

## 📚 Learn More

- [IRC Basics](https://www.irchelp.org/)
- [Libera.Chat Guide](https://libera.chat/guides/)
- [IRC Command Reference](https://en.wikipedia.org/wiki/List_of_Internet_Relay_Chat_commands)

---

**Happy chatting!** 🎉
