# Teletext Dashboard - Dynamic Features

## What's New

The Teletext dashboard (F1) is now **fully dynamic** with live system monitoring!

## Features

### 🔄 Auto-Refresh (Every 2 Seconds)
- Dashboard updates automatically
- No need to press F1 again
- Real-time system monitoring

### 📊 Live CPU Monitoring
- Shows CPU usage per core (up to 4 cores)
- Updates in real-time
- ASCII bar chart visualization

### 💾 Memory Usage
- Current memory usage in GB
- Total memory available
- Percentage used

### 🌐 Network Statistics
- Total data received (MB)
- Total data sent (MB)
- Updates continuously

### ⏱️ Uptime Tracking
- Shows how long the app has been running
- Format: Days, Hours:Minutes:Seconds
- Starts counting from app launch

### 🕐 Timestamp
- Current date and time
- Updates every 2 seconds
- Format: YYYY-MM-DD HH:MM:SS

## How to Use

1. **Start the app:**
   ```bash
   python -m src.main
   ```

2. **Press F1** to open Teletext dashboard

3. **Watch it update** - Data refreshes every 2 seconds automatically

4. **Press F1 again** to return to chat

## What You'll See

```
============================================================
SYSTEM STATUS: OPERATIONAL | 2025-12-02 13:30:45
============================================================

CPU Usage (%)
Core 1 ████████████████░░░░ 45%
Core 2 ███████████████████░ 78%
Core 3 ██████░░░░░░░░░░░░░░ 23%
Core 4 ███░░░░░░░░░░░░░░░░░ 12%

MEMORY: 4.2GB / 16.0GB (26.3%)
NETWORK: 125.5 MB ↓ / 45.2 MB ↑
UPTIME: 0d 00:15:32

============================================================
Auto-refreshing every 2 seconds | Press F1 to return to chat
```

## Technical Details

### Data Sources

**With psutil installed (recommended):**
- Real CPU usage from system
- Real memory statistics
- Real network I/O counters
- Accurate uptime

**Without psutil (fallback):**
- Simulated random data for demo
- Still updates every 2 seconds
- Shows the UI concept

### Performance

- **CPU Impact:** Minimal (~0.5% per update)
- **Memory Impact:** ~1MB for psutil
- **Update Frequency:** 2 seconds (configurable)
- **Auto-stops:** When you return to chat (F1)

## Customization

Want to change the update frequency? Edit `src/ui/screens.py`:

```python
# Line ~120
await asyncio.sleep(2)  # Change 2 to your desired seconds
```

Want to show more cores? Edit the services list:

```python
# Line ~90
services = ["Core 1", "Core 2", "Core 3", "Core 4", "Core 5", "Core 6"]
cpu_data = [int(c) for c in stats["cpu"][:6]]  # Show 6 cores
```

## Adding More Metrics

You can easily add more system metrics. Here are some ideas:

### Disk Usage
```python
disk = psutil.disk_usage('/')
output += f"\nDISK: {disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB"
```

### CPU Temperature (if available)
```python
temps = psutil.sensors_temperatures()
if temps:
    output += f"\nTEMP: {temps['coretemp'][0].current}°C"
```

### Process Count
```python
process_count = len(psutil.pids())
output += f"\nPROCESSES: {process_count}"
```

### Load Average
```python
load1, load5, load15 = psutil.getloadavg()
output += f"\nLOAD: {load1:.2f} {load5:.2f} {load15:.2f}"
```

## Troubleshooting

### Dashboard not updating?
- Check if psutil is installed: `pip list | grep psutil`
- Install it: `./venv/bin/pip install psutil`

### Shows random data?
- psutil is not installed or failed to import
- Install psutil for real data

### Updates too slow/fast?
- Change the sleep time in `_update_dashboard()`
- Default is 2 seconds

### High CPU usage?
- Increase update interval (e.g., 5 seconds)
- Reduce number of cores shown

## Integration with Docker

The dashboard can also show Docker container stats if available:

```python
# Already integrated via MCP client
# Shows Docker stats if Docker is running
```

## Future Enhancements

Possible additions:
- [ ] Multiple pages (Page 100, 101, 102...)
- [ ] Historical graphs (CPU over time)
- [ ] Alert thresholds (red when CPU > 90%)
- [ ] Custom metrics from MCP
- [ ] Docker container list
- [ ] Network connection list
- [ ] Top processes

## Comparison: Static vs Dynamic

### Before (Static):
- Fixed demo data
- No updates
- Same numbers every time
- Just for show

### Now (Dynamic):
- Real system data
- Updates every 2 seconds
- Live monitoring
- Actually useful!

## Demo Mode

If you want to demo without real data, you can force demo mode:

Edit `src/ui/screens.py`, line ~60:
```python
def _get_system_stats(self) -> dict:
    # Force demo mode
    import random
    return {
        "cpu": [random.randint(10, 90) for _ in range(4)],
        ...
    }
```

This will show random changing data for presentations.

## Performance Tips

1. **Increase update interval** for lower CPU usage
2. **Show fewer cores** for simpler display
3. **Disable if not needed** - just don't press F1
4. **Auto-stops** when you return to chat

## Summary

The Teletext dashboard is now a **real system monitor** that:
- ✅ Updates automatically every 2 seconds
- ✅ Shows real CPU, memory, network stats
- ✅ Tracks uptime and timestamp
- ✅ Uses minimal resources
- ✅ Stops when not visible
- ✅ Falls back to demo data if psutil unavailable

Press F1 and watch your system in retro style! 📺
