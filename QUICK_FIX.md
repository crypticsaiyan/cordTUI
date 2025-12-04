# Quick Fix for Your Docker Permission Issue

## The Problem

You're seeing "No Docker containers found" even though `sudo docker ps` shows your nginx container running.

## The Solution (Choose One)

### Option 1: Automated Fix (Recommended)

```bash
./fix_docker_permissions.sh
```

Then **log out and log back in** to your system.

### Option 2: Manual Fix

```bash
# Add yourself to docker group
sudo usermod -aG docker $USER

# Log out and log back in
# (or run: newgrp docker for temporary access)
```

### Option 3: Quick Test (Temporary)

```bash
# This gives you docker access in current shell only
newgrp docker

# Now test
python3 test_health_bot.py
```

## Verify It Works

After applying the fix:

```bash
# This should work WITHOUT sudo
docker ps

# You should see your nginx container
```

## Test the Health Bot

```bash
# Test the bot
python3 test_health_bot.py

# Or in the TUI
python demo.py
# Then type: /ai
```

## Expected Output

```
🏥 Docker Health Check
========================================
🟢 Summary: 1 healthy, 0 warning, 0 critical

Details:
✅ quizzical_nobel: RUNNING, up 1m, restarts=0
```

## Why This Happens

Docker requires special permissions to access `/var/run/docker.sock`. Adding your user to the `docker` group grants this permission.

## Still Having Issues?

See the detailed guide: [FIX_DOCKER_PERMISSIONS.md](FIX_DOCKER_PERMISSIONS.md)
