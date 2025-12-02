# Cord-TUI Documentation Index

Welcome to Cord-TUI! This index will guide you through all the documentation.

## 🚀 Getting Started

Start here if you're new to the project:

1. **[README.md](README.md)** - Project overview and quick introduction
2. **[QUICKSTART.md](QUICKSTART.md)** - Installation and first steps
3. **[setup.sh](setup.sh)** - Automated setup script

## 📚 Core Documentation

### For Users
- **[QUICKSTART.md](QUICKSTART.md)** - How to install and run
- **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** - Presentation guide for demos
- **[TELETEXT_PAGE_100.md](TELETEXT_PAGE_100.md)** - Teletext dashboard guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

### For Developers
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture deep dive
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview
- **[COMPARISON.md](COMPARISON.md)** - How Cord-TUI compares to alternatives

### For Testing
- **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** - Comprehensive testing guide
- **[demo.py](demo.py)** - Demo simulation script

## 📁 Project Structure

```
cord-tui/
├── 📄 Documentation
│   ├── README.md              # Main readme
│   ├── QUICKSTART.md          # Getting started
│   ├── ARCHITECTURE.md        # Technical details
│   ├── PROJECT_SUMMARY.md     # Complete overview
│   ├── DEMO_SCRIPT.md         # Presentation guide
│   ├── COMPARISON.md          # Feature comparison
│   ├── TROUBLESHOOTING.md     # Problem solving
│   ├── TESTING_CHECKLIST.md   # Testing guide
│   └── INDEX.md               # This file
│
├── 🎨 Assets
│   ├── logo.txt               # ASCII logo
│   └── demo.txt               # Sample file for demos
│
├── ⚙️ Configuration
│   └── .cord/
│       └── config.json        # App configuration
│
├── 💻 Source Code
│   └── src/
│       ├── main.py            # Entry point
│       ├── core/              # Backend logic
│       │   ├── irc_client.py  # IRC connection
│       │   ├── mcp_client.py  # AI integration
│       │   ├── wormhole.py    # File transfer
│       │   └── audio.py       # Sound engine
│       └── ui/                # Frontend
│           ├── app.py         # Main app
│           ├── styles.tcss    # CSS styling
│           ├── screens.py     # Teletext screen
│           └── widgets/       # UI components
│
├── 🛠️ Setup
│   ├── requirements.txt       # Python dependencies
│   ├── setup.sh              # Setup script
│   └── .gitignore            # Git ignore rules
│
└── 🎬 Demo
    └── demo.py               # Demo simulation
```

## 🎯 Quick Navigation

### I want to...

**...install and run the app**
→ [QUICKSTART.md](QUICKSTART.md)

**...understand the architecture**
→ [ARCHITECTURE.md](ARCHITECTURE.md)

**...prepare a demo/presentation**
→ [DEMO_SCRIPT.md](DEMO_SCRIPT.md)

**...fix a problem**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**...test the features**
→ [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)

**...compare with other tools**
→ [COMPARISON.md](COMPARISON.md)

**...get a complete overview**
→ [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## 🎨 Key Features

### 1. Discord-Like Interface
Beautiful 3-pane layout with channels, chat, and members.
- **Code**: `src/ui/app.py`, `src/ui/styles.tcss`
- **Docs**: [ARCHITECTURE.md](ARCHITECTURE.md#ui-layer)

### 2. Teletext Dashboard (F1) - Page 100
Authentic 1980s Ceefax/Oracle aesthetic with modern DevOps data.
- **Code**: `src/ui/screens.py`
- **Docs**: [TELETEXT_PAGE_100.md](TELETEXT_PAGE_100.md)
- **Preview**: [assets/teletext_preview.txt](assets/teletext_preview.txt)

### 3. Wormhole File Transfer
Peer-to-peer encrypted file transfers.
- **Code**: `src/core/wormhole.py`
- **Docs**: [ARCHITECTURE.md](ARCHITECTURE.md#wormholepy)

### 4. Geiger Counter Audio
Audio feedback for log events.
- **Code**: `src/core/audio.py`
- **Docs**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md#4-geiger-counter-audio)

### 5. MCP Integration
AI-powered commands via Model Context Protocol.
- **Code**: `src/core/mcp_client.py`
- **Docs**: [ARCHITECTURE.md](ARCHITECTURE.md#mcp_clientpy)

## 📖 Reading Order

### For First-Time Users
1. README.md - Get the big picture
2. QUICKSTART.md - Install and run
3. Play with the app!
4. TROUBLESHOOTING.md - If you hit issues

### For Hackathon Judges
1. **TELETEXT_JUDGES_GUIDE.md** - Why the Teletext dashboard wins
2. PROJECT_SUMMARY.md - Complete overview
3. COMPARISON.md - Why it's innovative
4. ARCHITECTURE.md - Technical execution
5. Watch the demo or read DEMO_SCRIPT.md

### For Developers
1. ARCHITECTURE.md - Understand the design
2. Browse `src/` - Read the code
3. TESTING_CHECKLIST.md - Test everything
4. Extend and customize!

## 🔧 Configuration Files

- **`.cord/config.json`** - Server settings, theme, audio
- **`src/ui/styles.tcss`** - CSS-like styling
- **`requirements.txt`** - Python dependencies

## 🎬 Demo Files

- **`demo.py`** - Simulates server death for audio demo
- **`assets/demo.txt`** - Sample file for wormhole demo
- **`assets/logo.txt`** - ASCII art logo

## 📝 Documentation Standards

All documentation follows these principles:
- **Clear**: Easy to understand
- **Concise**: No unnecessary fluff
- **Complete**: Covers all features
- **Current**: Kept up to date

## 🤝 Contributing

Want to contribute? Here's how:

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the design
2. Check [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) for testing
3. Follow the existing code style
4. Update documentation for new features

## 📊 Project Stats

- **Lines of Code**: ~1,500
- **Files**: 25+
- **Dependencies**: 7 core libraries
- **Memory Usage**: ~20MB
- **Startup Time**: <1 second

## 🏆 Hackathon Theme: "Resurrection"

This project resurrects three dead technologies:

1. **Teletext** (1980s TV pages) → Modern dashboard
2. **DCC** (IRC file transfer) → Secure P2P
3. **Beeping computers** → Audio monitoring

Read more in [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md#the-three-resurrections)

## 🔗 External Resources

- **Textual Framework**: https://textual.textualize.io/
- **bottom (IRC)**: https://github.com/numberoverzero/bottom
- **magic-wormhole**: https://github.com/magic-wormhole/magic-wormhole
- **MCP**: https://modelcontextprotocol.io/

## 📞 Support

Having issues? Check these in order:

1. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common problems
2. [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) - Verify setup
3. GitHub Issues - Report bugs
4. Textual Discord - Framework help

## 🎓 Learning Path

### Beginner
1. Install and run the app
2. Try basic commands
3. Toggle Teletext (F1)
4. Send a test message

### Intermediate
1. Connect to real IRC server
2. Try wormhole file transfer
3. Execute MCP commands
4. Customize the theme

### Advanced
1. Add new MCP tools
2. Create custom widgets
3. Extend the audio engine
4. Build new screens

## 📅 Version History

- **v0.1.0** - Initial release
  - Discord-like UI
  - IRC integration
  - Teletext dashboard
  - Wormhole transfers
  - Geiger counter audio
  - MCP integration

## 🎯 Future Roadmap

See [ARCHITECTURE.md](ARCHITECTURE.md#future-enhancements) for planned features:
- Multi-server support
- Plugin system
- Custom themes
- Desktop notifications
- Persistent logging

## 📜 License

[Add your license here]

## 🙏 Acknowledgments

Built with:
- Textual by Textualize
- bottom by numberoverzero
- magic-wormhole by Brian Warner
- And the amazing Python community

---

**Last Updated**: December 2, 2025  
**Version**: 0.1.0  
**Status**: Ready for demo 🚀
