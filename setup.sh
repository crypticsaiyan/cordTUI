#!/bin/bash
# Cord-TUI Setup Script with Azure Integration

echo "🚀 Setting up Cord-TUI with Azure Integration..."
echo "=========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "🔍 Checking optional dependencies..."
echo "=========================================="

# Check for audio support
if ! python3 -c "import simpleaudio" 2>/dev/null; then
    echo "⚠️  Audio support not available. Install system dependencies:"
    echo "   Ubuntu/Debian: sudo apt-get install python3-dev libasound2-dev"
    echo "   macOS: brew install portaudio"
else
    echo "✓ Audio support available"
fi

# Check for wormhole
if ! command -v wormhole &> /dev/null; then
    echo "⚠️  magic-wormhole not found in PATH. File transfers may not work."
    echo "   Install with: pip install magic-wormhole"
else
    echo "✓ magic-wormhole available"
fi

# Check for Docker (for MCP demo)
if ! command -v docker &> /dev/null; then
    echo "ℹ️  Docker not found. MCP docker-stats command will not work."
else
    echo "✓ Docker available"
fi

# Check for Azure SDK
echo ""
echo "=========================================="
echo "🔵 Checking Azure Integration..."
echo "=========================================="

if python3 -c "import azure.identity, azure.mgmt.containerinstance" 2>/dev/null; then
    echo "✓ Azure SDK installed"
    
    # Check for .env file
    if [ -f ".env" ]; then
        echo "✓ .env file exists"
        
        # Check if Azure credentials are configured
        if grep -q "AZURE_SUBSCRIPTION_ID=your-subscription-id" .env 2>/dev/null || \
           ! grep -q "AZURE_SUBSCRIPTION_ID=" .env 2>/dev/null; then
            echo "⚠️  Azure credentials not configured in .env"
            echo ""
            echo "To enable Azure Container Instance monitoring:"
            echo "1. Create Azure Service Principal:"
            echo "   az ad sp create-for-rbac --name \"kiro-irc-bot-sp\" \\"
            echo "     --role Reader \\"
            echo "     --scopes /subscriptions/YOUR_SUB_ID/resourceGroups/YOUR_RG \\"
            echo "     --sdk-auth"
            echo ""
            echo "2. Edit .env file with the credentials from step 1"
            echo "3. See AZURE_SETUP_GUIDE.md for detailed instructions"
        else
            echo "✓ Azure credentials configured"
            echo ""
            echo "Testing Azure connection..."
            if python3 test_azure_connection.py 2>/dev/null; then
                echo "✅ Azure integration ready!"
            else
                echo "⚠️  Azure connection test failed. Check credentials in .env"
            fi
        fi
    else
        echo "⚠️  .env file not found"
        echo "Creating .env from template..."
        cp .env.example .env
        echo "✓ Created .env file"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env file with your Azure credentials!"
        echo "   See AZURE_SETUP_GUIDE.md for instructions"
    fi
else
    echo "✓ Azure SDK installed (required for Azure integration)"
fi

# Check for Azure CLI
echo ""
if command -v az &> /dev/null; then
    echo "✓ Azure CLI installed"
else
    echo "ℹ️  Azure CLI not found (optional, needed for setup only)"
    echo "   Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
fi

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "To run Cord-TUI:"
echo "  source venv/bin/activate"
echo "  python -m src.main"
echo ""
echo "Features:"
echo "  • IRC chat interface with channels"
echo "  • Teletext dashboard (Press F1)"
echo "  • File transfers via magic-wormhole"
echo "  • AI commands with /ai"
echo "  • Azure Container Instance monitoring (if configured)"
echo ""
echo "Azure Integration:"
echo "  • /ai list containers - List Azure containers"
echo "  • /ai show status - Container status"
echo "  • /ai what are the IPs? - IP addresses"
echo "  • /ai show resources - CPU/Memory info"
echo "  • See ENHANCED_QUERIES_GUIDE.md for all commands"
echo ""
echo "Setup Azure (if not done):"
echo "  1. Read: AZURE_SETUP_GUIDE.md"
echo "  2. Create Service Principal"
echo "  3. Edit .env file"
echo "  4. Test: python3 test_azure_connection.py"
echo ""
echo "Documentation:"
echo "  • README.md - Main documentation"
echo "  • AZURE_SETUP_GUIDE.md - Azure setup"
echo "  • ENHANCED_QUERIES_GUIDE.md - AI commands"
echo "  • STATUS_VS_HEALTH.md - Status vs health checks"
echo ""
echo "=========================================="
