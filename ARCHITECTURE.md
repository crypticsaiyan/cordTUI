# Phosphor Architecture

## Overview

Phosphor is a terminal-based IRC client that combines the lightweight IRC protocol with modern UX design. It's built with Python using Textual for the UI and integrates three "resurrection" features that bring back dead tech concepts with modern improvements.

## Tech Stack

- **Language**: Python 3.11+
- **UI Framework**: Textual (Modern TUI framework)
- **Network**: bottom (AsyncIO IRC library)
- **AI**: MCP (Model Context Protocol)
- **File Transfer**: magic-wormhole (P2P encrypted transfers)
- **Audio**: simpleaudio (Log sonification)
- **Visualization**: plotext (ASCII charts)

## Architecture Layers

### 1. Core Layer (`src/core/`)

Backend business logic, completely decoupled from UI.

#### `irc_client.py`
- Wraps the `bottom` async IRC library
- Handles connection, authentication, channel joining
- Provides callback mechanism for incoming messages
- Non-blocking async design integrates with Textual's event loop

#### `mcp_client.py`
- Model Context Protocol integration
- Executes "AI" commands like `/ai docker-stats`
- Extensible tool registry pattern
- Returns structured JSON responses

#### `wormhole.py`
- Wraps `magic-wormhole` for P2P file transfers
- Generates human-readable codes (e.g., "7-guitar-ocean")
- Async subprocess management
- Status callbacks for UI updates

#### `audio.py`
- The "Geiger Counter" sound engine
- Maps log levels to audio frequencies
- Thread-safe audio playback
- Tracks error rates for escalating sounds

### 2. UI Layer (`src/ui/`)

Textual-based frontend, completely decoupled from backend.

#### `app.py`
- Main Textual App class
- Orchestrates all components
- Handles keybindings (F1 for Teletext)
- Routes commands to appropriate backend services
- Thread-safe message passing between IRC and UI

#### `styles.tcss`
- CSS-like styling for Textual
- Modern color palette (#36393f, #5865F2)
- Responsive grid layout
- Embed styling with colored borders

#### `screens.py`
- **TeletextScreen**: The retro dashboard
- Uses plotext for ASCII bar charts
- Fetches live data from MCP
- F1 toggles between chat and teletext

#### `widgets/`
Custom reusable components:

- **chat_pane.py**: Message stream with Markdown support
- **sidebar.py**: Channel tree and member list
- **embed.py**: Rich message cards

### 3. Configuration Layer (`.phosphor/`)

- `config.json`: Server settings, theme, audio preferences
- `sounds/`: Custom audio samples (future)

## Data Flow

### Message Flow (IRC → UI)
```
IRC Server → bottom → irc_client.py → callback → app.py → chat_pane.py → UI
                                          ↓
                                      audio.py (parallel)
```

### Command Flow (User → Backend)
```
User Input → app.py → parse command → route to:
                                      ├─ irc_client.py (/msg)
                                      ├─ mcp_client.py (/ai)
                                      └─ wormhole.py (/send, /grab)
```

### Teletext Flow (F1 Press)
```
F1 → app.py → push_screen(TeletextScreen) → mcp_client.py → docker stats → plotext → render
```

## Key Design Patterns

### 1. Callback Pattern
Backend services use callbacks to push data to UI without tight coupling:
```python
irc.set_message_callback(self._on_irc_message)
wormhole.set_status_callback(self._on_wormhole_status)
```

### 2. Async/Await
All network operations are async to prevent blocking the UI:
```python
asyncio.create_task(self._connect_irc())
```

### 3. Thread-Safe UI Updates
IRC runs in background, UI updates use `call_from_thread`:
```python
self.call_from_thread(self.chat_pane.add_message, nick, message)
```

### 4. Screen Stack
Textual's screen stack for modal views:
```python
self.push_screen(TeletextScreen())  # F1
self.pop_screen()                    # F1 again
```

## The Three Resurrections

### 1. Teletext Dashboard
**Dead Tech**: Ceefax/Teletext (1980s TV information pages)  
**Modern Problem**: Heavy web dashboards (Grafana, Datadog)  
**Solution**: ASCII dashboard with live metrics, zero latency

**Implementation**:
- plotext for bar charts
- MCP fetches Docker stats
- Bright neon colors on black background
- Instant toggle with F1

### 2. DCC 2.0 (Wormhole)
**Dead Tech**: IRC DCC (Direct Client-to-Client file transfer)  
**Modern Problem**: Cloud uploads (security risk, slow)  
**Solution**: Peer-to-peer encrypted tunnels

**Implementation**:
- magic-wormhole library
- Human-readable codes
- No server, no traces
- Simple UX: `/send` and `/grab`

### 3. Geiger Counter
**Dead Tech**: Beeping motherboards, clicking hard drives  
**Modern Problem**: Silent failures  
**Solution**: Log sonification

**Implementation**:
- Map log levels to frequencies
- Background listener on message stream
- Escalating sounds for increasing error rates
- Sensory feedback before visual inspection

## Performance Characteristics

- **Memory**: ~20MB (vs 2GB for typical chat apps)
- **Startup**: <1 second
- **Latency**: Near-zero (terminal rendering)
- **Network**: Minimal (IRC protocol is text-based)

## Extension Points

### Adding MCP Tools
Edit `src/core/mcp_client.py`:
```python
self.tools["new-command"] = self._new_command

async def _new_command(self, args):
    # Your logic here
    return {"result": "data"}
```

### Custom Themes
Edit `src/ui/styles.tcss` with CSS-like syntax.

### Audio Samples
Add `.wav` files to `.phosphor/sounds/` and reference in `audio.py`.

### New Screens
Create in `src/ui/screens.py` and bind to keys in `app.py`.

## Testing Strategy

1. **Unit Tests**: Core logic (IRC, MCP, Wormhole)
2. **Integration Tests**: UI interactions with Textual's test harness
3. **Demo Script**: `demo.py` for live demonstrations
4. **Manual Testing**: Real IRC servers

## Deployment

Single-file executable possible with PyInstaller:
```bash
pyinstaller --onefile src/main.py
```

## Future Enhancements

1. **Multi-server support**: Connect to multiple IRC networks
2. **Plugin system**: Load custom MCP tools dynamically
3. **Themes**: User-selectable color schemes
4. **Notifications**: Desktop notifications for mentions
5. **Logging**: Persistent chat history
6. **Encryption**: E2E encryption for DMs
