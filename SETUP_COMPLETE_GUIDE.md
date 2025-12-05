# Complete Setup Guide - Cord-TUI with Azure Integration

## Quick Setup (3 Steps)

### Step 1: Run Setup Script

```bash
./setup.sh
```

This will:
- ✅ Create virtual environment
- ✅ Install all dependencies (including Azure SDK)
- ✅ Create .env file from template
- ✅ Check Azure configuration
- ✅ Test Azure connection (if configured)

### Step 2: Configure Azure (Optional)

If you want Azure Container Instance monitoring:

**A. Create Azure Service Principal:**

```bash
az login
az ad sp create-for-rbac \
  --name "kiro-irc-bot-sp" \
  --role Reader \
  --scopes /subscriptions/YOUR_SUB_ID/resourceGroups/YOUR_RG \
  --sdk-auth
```

**B. Edit .env file:**

```bash
nano .env
```

Fill in the values from step A:
```env
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_RESOURCE_GROUP=your-resource-group
```

**C. Test connection:**

```bash
python3 test_azure_connection.py
```

### Step 3: Run the App

```bash
source venv/bin/activate
python -m src.main
```

That's it! 🎉

## What You Get

### IRC Chat Interface
- Connect to IRC servers
- Join/leave channels
- Send/receive messages
- Private messages
- Channel search

### AI Commands
Type `/ai` followed by your question:

**Without Azure:**
- `/ai docker health` - Check local Docker containers
- `/ai system-info` - System information
- `/ai list-files` - File operations

**With Azure (if configured):**
- `/ai list containers` - List Azure containers
- `/ai show status` - Container status
- `/ai what are the IPs?` - IP addresses
- `/ai show ports` - Port information
- `/ai show resources` - CPU/Memory
- `/ai check health` - Health checks
- See ENHANCED_QUERIES_GUIDE.md for all commands

### Teletext Dashboard
- Press F1 to toggle
- Real-time container monitoring
- System statistics
- Visual dashboard

### File Transfers
- `/grab` command
- Uses magic-wormhole
- Secure peer-to-peer transfers

## Setup Details

### What setup.sh Does

1. **Checks Python version** - Requires Python 3.8+
2. **Creates virtual environment** - Isolated Python environment
3. **Installs dependencies** - All required packages
4. **Checks optional features:**
   - Audio support (for notifications)
   - magic-wormhole (for file transfers)
   - Docker (for local container monitoring)
   - Azure SDK (for Azure integration)
   - Azure CLI (for setup only)
5. **Creates .env file** - Configuration template
6. **Tests Azure connection** - If credentials configured

### Dependencies Installed

**Core:**
- textual - TUI framework
- miniirc - IRC client
- rich - Terminal formatting

**Azure (for container monitoring):**
- azure-identity - Authentication
- azure-mgmt-containerinstance - Container management
- azure-mgmt-resource - Resource management

**Optional:**
- simpleaudio - Audio notifications
- magic-wormhole - File transfers
- plotext - Charts in terminal

### Configuration Files

**`.env`** - Your configuration (created from .env.example)
```env
# Azure credentials (optional)
AZURE_SUBSCRIPTION_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
AZURE_TENANT_ID=...
AZURE_RESOURCE_GROUP=...

# IRC settings (optional)
IRC_SERVER=irc.libera.chat
IRC_PORT=6667
IRC_CHANNELS=#your-channel
```

## Troubleshooting

### "Python not found"
Install Python 3.8 or higher:
```bash
# Ubuntu/Debian
sudo apt install python3 python3-venv python3-pip

# macOS
brew install python3
```

### "pip install failed"
Update pip:
```bash
python3 -m pip install --upgrade pip
```

### "Azure SDK not installed"
Run setup again:
```bash
./setup.sh
```

Or install manually:
```bash
pip install azure-identity azure-mgmt-containerinstance azure-mgmt-resource
```

### "Azure connection test failed"
Check your .env file:
```bash
cat .env | grep AZURE
```

Verify credentials:
```bash
az login --service-principal \
  --username $AZURE_CLIENT_ID \
  --password $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID
```

### "Audio support not available"
Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev libasound2-dev

# macOS
brew install portaudio
```

Then reinstall:
```bash
pip install simpleaudio
```

## Advanced Setup

### Running as System Service

```bash
sudo ./install_service.sh
sudo systemctl start kiro-azure-bot
```

### Custom Configuration

Edit `.env` file for custom settings:
- IRC server and channels
- Azure resource group
- Bot nickname
- Rate limiting

### Multiple Resource Groups

To monitor multiple resource groups, you'll need to:
1. Create separate .env files
2. Run multiple instances
3. Or modify the code to support multiple groups

## Documentation

- **README.md** - Main documentation
- **AZURE_SETUP_GUIDE.md** - Detailed Azure setup
- **ENHANCED_QUERIES_GUIDE.md** - All AI commands
- **STATUS_VS_HEALTH.md** - Status vs health checks
- **AZURE_INTEGRATION_COMPLETE.md** - Integration details

## Quick Reference

**Setup:**
```bash
./setup.sh
```

**Run:**
```bash
source venv/bin/activate
python -m src.main
```

**Test Azure:**
```bash
python3 test_azure_connection.py
```

**Update dependencies:**
```bash
pip install -r requirements.txt --upgrade
```

## Next Steps

1. ✅ Run `./setup.sh`
2. ✅ Configure Azure (optional)
3. ✅ Run `python -m src.main`
4. ✅ Join IRC channel
5. ✅ Try `/ai list containers`

Enjoy! 🚀
