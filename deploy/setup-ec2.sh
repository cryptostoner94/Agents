#!/usr/bin/env bash
# NEXUS OMEGA - AWS EC2 Setup Script
# Run this once on a fresh EC2 instance to set up the entire deployment

set -e

echo "========================================="
echo "  NEXUS OMEGA - EC2 Setup"
echo "========================================="
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ] && [ "$SUDO_USER" == "" ]; then
    echo "Please run with sudo: sudo bash setup-ec2.sh"
    exit 1
fi

USER_NAME="${SUDO_USER:-$(whoami)}"
USER_HOME=$(getent passwd "$USER_NAME" | cut -d: -f6)

echo "[1/7] Creating app directory..."
sudo mkdir -p /opt/nexus-omega
sudo chown "$USER_NAME:$USER_NAME" /opt/nexus-omega

echo "[2/7] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip git curl

echo "[3/7] Installing Python packages..."
pip3 install --upgrade pip -q
pip3 install fastapi uvicorn pydantic playwright requests httpx beautifulsoup4 lxml aiofiles -q

echo "[4/7] Installing Playwright Chromium..."
python3 -m playwright install chromium 2>/dev/null || echo "  (Playwright install may need more time)"

echo "[5/7] Creating systemd services..."
sudo cp deploy/nexus-omega.service /etc/systemd/system/
sudo cp deploy/nexus-webhook.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "[6/7] Setting up webhook server..."
# Enable webhook port in firewall (if ufw is active)
sudo ufw allow 8443/tcp 2>/dev/null || true

echo "[7/7] Creating startup script..."
cat > /opt/nexus-omega/start.sh << 'STARTEOF'
#!/usr/bin/env bash
cd /opt/nexus-omega
sudo systemctl start nexus-omega
sudo systemctl start nexus-webhook
echo "NEXUS OMEGA started. Check status with: sudo systemctl status nexus-omega"
curl -s http://127.0.0.1:8000/health
STARTEOF
chmod +x /opt/nexus-omega/start.sh

echo ""
echo "========================================="
echo "  EC2 Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Set up environment variables:"
echo "   Create /opt/nexus-omega/.env with your API keys"
echo "   (Copy from .env.template)"
echo ""
echo "2. Add webhook secret for GitHub:"
echo "   export NEXUS_WEBHOOK_SECRET='your-secret'"
echo ""
echo "3. Clone your repository:"
echo "   git clone https://github.com/youruser/yourrepo.git /opt/nexus-omega"
echo ""
echo "4. Start services:"
echo "   bash /opt/nexus-omega/start.sh"
echo ""
echo "5. Add GitHub webhook:"
echo "   URL: https://YOUR-EC2-IP:8443/webhook"
echo "   Secret: your-webhook-secret"
echo "   Events: Push"
echo ""
echo "For HTTPS (recommended), set up nginx with letsencrypt"
echo ""
echo "========================================="