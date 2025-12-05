# phosphor

> Discord UX + IRC Protocol = Terminal Magic

A resurrection of IRC with Discord's user experience, running in a high-performance Terminal UI. Proves that modern collaboration doesn't need 2GB of RAM—it just needs better design.

## 🚀 Quick Start

```bash
# Setup (one time)
./setup.sh

# Run
python -m src.main

# Try it
# - Chat in real IRC channels (#python, #linux, #programming)
# - See live member lists in the sidebar
# - Press F1 for Teletext dashboard
# - Type /ai docker-stats
# - Type /send demo.txt

# Test IRC connection
python test_public_irc.py
```
![alt text](image.png)


## ✨ Features

### 🎨 Discord-Like Interface
Beautiful 3-pane layout with channels, chat, and members. Markdown support, syntax highlighting, and rich embeds.

### 📺 Teletext Dashboard (F1) - Page 100
Authentic 1980s Ceefax/Oracle aesthetic with modern DevOps data. Features:
- Ticking clock (seconds update in real-time)
- ASCII CPU/Memory graphs using `psutil`
- Container status matrix with colored blocks
- Git commits as "Breaking News" headlines
- Scrolling ticker tape with error logs
- Strict 8-color palette (Black, White, Red, Green, Blue, Cyan, Magenta, Yellow)
- Block graphics (█ ▀ ▄ ░) for authentic retro feel

![alt text](image-1.png)

See [TELETEXT_PAGE_100.md](TELETEXT_PAGE_100.md) for full details.

### 🔐 Wormhole File Transfer
Peer-to-peer encrypted file transfers with human-readable codes. No cloud, no traces, just magic.

![alt text](image-2.png)
![alt text](image-4.png)

### 🔊 Geiger Counter Audio
Audio feedback for system health. Hear errors before you see them. Escalating sounds for increasing error rates.

### 🤖 MCP Integration
AI-powered commands via Model Context Protocol. Extensible tool system for automation.

![alt text](image-3.png)

## 📊 Performance

| Metric | Discord | phosphor |
|--------|---------|----------|
| Memory | 2GB | 20MB |
| Startup | 10s | <1s |
| CPU | 10% | 2% |
| Protocol | Proprietary | Open (IRC) |

**100x more efficient. Same great UX.**

## 🎯 The Three Resurrections

This project resurrects three "dead" technologies with modern improvements:

1. **Teletext** (1980s TV pages) → Zero-latency dashboard
2. **DCC** (IRC file transfer) → Secure P2P with easy UX
3. **Beeping computers** → Audio monitoring system

## 📚 Documentation

- **[START_HERE.md](START_HERE.md)** - Quick guide to get started
- **[QUICKSTART.md](QUICKSTART.md)** - Detailed installation
- **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** - Presentation guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical deep dive
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Problem solving
- **[INDEX.md](INDEX.md)** - Complete navigation

## 🎮 Commands

| Command | Description |
|---------|-------------|
| `F1` | Toggle Teletext Dashboard |
| `/send <file>` | Send file via wormhole |
| `/grab <code>` | Receive file via wormhole |
| `/ai [query]` | DevOps Health Bot - Check Docker containers |

## 🤖 DevOps Health Bot

phosphor includes an AI-powered DevOps assistant that automatically monitors Docker container health:

```bash
# In the TUI or via IRC:
/ai                    # Check all containers
/ai prod               # Check production
/ai staging web        # Check staging web service
```

**Features:**
- 🏥 Automatic health assessment (healthy, warning, critical)
- 🔍 Smart filtering by environment (prod, staging) and service (web, api, db)
- 📊 Monitors status, health checks, restarts, CPU, memory
- 💬 IRC-friendly output with emojis and actionable recommendations
- 🔒 Read-only, safe operations

See [DEVOPS_HEALTH_BOT.md](DEVOPS_HEALTH_BOT.md) for full documentation.

## 🛠️ Tech Stack

- **Python 3.11+** - Language
- **Textual** - Modern TUI framework
- **bottom** - Async IRC library
- **magic-wormhole** - P2P file transfers
- **simpleaudio** - Audio feedback
- **plotext** - ASCII charts
- **MCP** - AI integration with Docker monitoring

## 🎬 Demo

```bash
# Run the full app with Teletext dashboard
./demo_teletext.sh

# Or run the error simulation (Geiger counter audio)
python demo.py
```

The Teletext demo shows off the authentic 1980s dashboard. The error simulation showcases the Geiger counter audio feature with increasing error rates.

## 📁 Project Structure

```
phosphor/
├── src/
│   ├── core/          # Backend (IRC, MCP, Wormhole, Audio)
│   └── ui/            # Frontend (Textual TUI)
├── .phosphor/         # Configuration
├── assets/            # Logo and demo files
└── docs/              # 10+ comprehensive guides
```

## 🏆 Why phosphor?

- **Efficient**: 1/100th the memory of Discord
- **Fast**: Sub-second startup, zero-latency UI
- **Open**: Built on IRC, the original open protocol
- **Innovative**: Only chat app with audio feedback
- **Beautiful**: Discord's UX in your terminal
- **Practical**: Actually solves real problems


---

**Built for the Resurrection Hackathon**  
*Proving that old tech + new design = magic* ✨
