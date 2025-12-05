# PHOSPHOR - Project Story

## Inspiration

We asked ourselves: **Why does chatting with your team need 2GB of RAM?**

Discord, Slack, Teams — they're all Electron apps consuming massive resources for what's essentially text communication. Meanwhile, IRC — the protocol that connected millions in the 90s — sits forgotten, dismissed as "outdated."

But IRC isn't dead. It's just waiting for better design.

We were also inspired by three "dead" technologies that solved real problems elegantly:
- **Teletext** (1980s TV information pages) — instant data, zero latency
- **DCC** (IRC's file transfer) — peer-to-peer, no cloud middleman  
- **Beeping computers** — auditory feedback before silent failures became the norm

What if we could resurrect all three with modern UX?

## What it does

**Phosphor** is a terminal-based IRC client that delivers Discord's user experience at $\frac{1}{100}$th the memory footprint.

| Metric | Discord | Phosphor |
|--------|---------|----------|
| Memory | 2GB | ~20MB |
| Startup | 10s | <1s |
| CPU idle | 10% | 2% |

Key features:
- **Discord-like 3-pane UI** — channels, chat, members with keyboard navigation
- **Teletext Dashboard (F1)** — authentic 1980s Ceefax aesthetic showing live DevOps metrics (CPU, memory, containers)
- **Wormhole File Transfer** — P2P encrypted transfers with human-readable codes like `7-guitar-ocean`
- **Geiger Counter Audio** — log sonification that lets you *hear* errors before you see them
- **MCP Integration** — AI-powered DevOps commands via `/ai docker-stats`

## How we built it

Built entirely in **4 days using Kiro** as our AI coding assistant.

**Tech Stack:**
- **Python 3.11+** — async-first architecture
- **Textual** — modern TUI framework for the Discord-like interface
- **miniirc** — lightweight async IRC library
- **magic-wormhole** — P2P encrypted file transfers
- **psutil** — system metrics for Teletext dashboard
- **MCP (Model Context Protocol)** — AI tool integration

**Architecture:**
```
┌─────────────────────────────────────────────────────┐
│                    UI Layer                         │
│  ┌─────────┐  ┌──────────┐  ┌─────────────────┐    │
│  │ Sidebar │  │ ChatPane │  │   MemberList    │    │
│  └────┬────┘  └────┬─────┘  └───────┬─────────┘    │
└───────┼────────────┼────────────────┼──────────────┘
        │            │                │
┌───────┴────────────┴────────────────┴──────────────┐
│                   Core Layer                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐  │
│  │IRCClient │ │MCPClient │ │ Wormhole │ │ Audio │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────┘  │
└─────────────────────────────────────────────────────┘
```

The callback pattern keeps UI and backend completely decoupled. IRC runs in a background thread with `call_from_thread` for thread-safe UI updates.

## Challenges we ran into

1. **Thread-safe UI updates** — IRC messages arrive on a background thread, but Textual's UI must be updated from the main thread. We solved this with Textual's `call_from_thread` mechanism.

2. **IRC nickname conflicts** — Public IRC servers often have nickname collisions. We implemented automatic retry with random suffixes when receiving `433 ERR_NICKNAMEINUSE`.

3. **Audio without dependencies** — Cross-platform audio is notoriously difficult. We generate WAV files in-memory and pipe them to system audio players (`paplay`, `aplay`, `afplay`) — no compiled dependencies needed.

4. **Teletext authenticity** — Recreating the 1980s Ceefax aesthetic required strict adherence to the 8-color palette and block graphics (`█ ▀ ▄ ░`). Modern terminals wanted to be *too* pretty.

5. **Wormhole integration** — `magic-wormhole` outputs codes to stderr in various formats. Parsing these reliably across different versions required careful regex handling.

## Accomplishments that we're proud of

- **100x efficiency gain** — Same UX, 1/100th the resources
- **Three resurrections in one app** — Teletext, DCC, and audio feedback all modernized
- **4-day build with Kiro** — From concept to polished product, including a complete Halloween theme (500+ lines of CSS generated by AI)
- **Zero cloud dependencies for file transfer** — True P2P with human-readable codes
- **The Geiger Counter** — You can literally *hear* your system's health

## What we learned

- **Old protocols aren't obsolete** — IRC's simplicity is a feature, not a bug
- **Terminal UIs can be beautiful** — Textual proves TUIs can rival web apps
- **AI pair programming accelerates everything** — Kiro helped us iterate faster than we thought possible
- **Constraints breed creativity** — The 8-color Teletext palette forced elegant design decisions

## What's next for PHOSPHOR

- **Multi-server support** — Connect to multiple IRC networks simultaneously
- **Plugin system** — Dynamic MCP tool loading for custom automation
- **E2E encryption** — Encrypted DMs using Signal protocol
- **Mobile companion** — Lightweight mobile client that syncs with desktop
- **Community themes** — User-contributed color schemes beyond Halloween 🎃

---

*Phosphor proves that the past isn't dead — it just needed better tools.* ✨
