#!/bin/bash
# AGENTS - Quick Setup Script for EC2
# Run this on a fresh EC2 instance

set -e

echo "========================================="
echo "  AGENTS - EC2 Setup"
echo "========================================="

# Get the directory where this script is
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/6] Creating directories..."
mkdir -p data/artifacts data/browser_screens data/state/sandbox

echo "[2/6] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip git curl -qq

echo "[3/6] Installing Python packages..."
pip3 install --upgrade pip -q
pip3 install fastapi uvicorn pydantic playwright requests httpx beautifulsoup4 lxml aiofiles -q

echo "[4/6] Installing Playwright..."
python3 -m playwright install chromium 2>/dev/null || true

echo "[5/6] Creating systemd service..."
sudo tee /etc/systemd/system/Agents.service > /dev/null << 'EOF'
[Unit]
Description=AGENTS AI Agent Platform
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Agents
Environment="NEXUS_BASE=/home/ubuntu/Agents/data"
ExecStart=/usr/bin/python3 -m uvicorn api_main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "[6/6] Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable Agents
sudo systemctl start Agents

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Check status:"
echo "  sudo systemctl status Agents"
echo ""
echo "View logs:"
echo "  sudo journalctl -u Agents -f"
echo ""
echo "Test:"
echo "  curl http://127.0.0.1:8000/health"
echo ""
echo "Open in browser:"
echo "  http://YOUR_EC2_IP:8000/chat"
echo "========================================="