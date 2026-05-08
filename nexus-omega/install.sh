#!/usr/bin/env bash
set -e

APP="/home/cryptostoner94/nexus-omega"
USER_NAME="cryptostoner94"

sudo systemctl stop nexus-omega || true
sudo mkdir -p "$APP/artifacts" "$APP/browser_screens"

sudo cp api_main.py "$APP/api_main.py"

sudo chown -R "$USER_NAME:$USER_NAME" "$APP"

cd "$APP"
python3 -m venv .venv
. .venv/bin/activate

pip install --upgrade pip
pip install fastapi uvicorn pydantic playwright
python -m playwright install chromium || true

python -m py_compile api_main.py

sudo tee /etc/systemd/system/nexus-omega.service >/dev/null <<EOF
[Unit]
Description=NEXUS OMEGA CLEAN CHAT FINAL
After=network-online.target

[Service]
Type=simple
User=cryptostoner94
WorkingDirectory=/home/cryptostoner94/nexus-omega
ExecStart=/home/cryptostoner94/nexus-omega/.venv/bin/uvicorn api_main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable nexus-omega
sudo systemctl restart nexus-omega

sleep 5

echo "HEALTH"
curl -s http://127.0.0.1:8000/health
echo ""

echo "CHAT TEST"
curl -s -X POST http://127.0.0.1:8000/api/chat \
-H "Content-Type: application/json" \
-d '{"message":"health status"}'
echo ""

echo "OPEN: http://136.114.174.54:8000/chat"
