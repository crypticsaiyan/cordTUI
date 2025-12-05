#!/bin/bash
# Install Kiro Azure IRC Bot as systemd service

set -e

echo "=========================================="
echo "Install Kiro Bot as systemd Service"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Get current directory and user
INSTALL_DIR=$(pwd)
CURRENT_USER=$(logname)

echo "Installation directory: $INSTALL_DIR"
echo "Running as user: $CURRENT_USER"
echo ""

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/kiro-azure-bot.service"

echo "Creating service file: $SERVICE_FILE"

cat > $SERVICE_FILE << EOF
[Unit]
Description=Kiro Azure IRC Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/kiro_azure_irc_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created"
echo ""

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload
echo "✅ Systemd reloaded"
echo ""

# Enable service
echo "Enabling service..."
systemctl enable kiro-azure-bot.service
echo "✅ Service enabled (will start on boot)"
echo ""

echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start kiro-azure-bot"
echo "  Stop:    sudo systemctl stop kiro-azure-bot"
echo "  Restart: sudo systemctl restart kiro-azure-bot"
echo "  Status:  sudo systemctl status kiro-azure-bot"
echo "  Logs:    sudo journalctl -u kiro-azure-bot -f"
echo ""
echo "To start now:"
echo "  sudo systemctl start kiro-azure-bot"
echo ""
