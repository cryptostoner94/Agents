#!/usr/bin/env bash
# AGENTS - GitHub Auto-Deploy Script
# Triggered by GitHub webhook or manual run

set -e

# ===== Configuration =====
REPO_URL="${AGENTS_REPO_URL:-}"
DEPLOY_KEY="${AGENTS_DEPLOY_KEY:-}"
APP_DIR="${AGENTS_APP_DIR:-/home/ubuntu/Agents}"
BRANCH="${AGENTS_BRANCH:-main}"
SERVICE_NAME="${AGENTS_SERVICE_NAME:-Agents}"

# Logging
LOG_FILE="/var/log/agents-deploy.log"
touch "$LOG_FILE"
exec >> "$LOG_FILE" 2>&1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# ===== Pre-flight Checks =====
log "===== AGENTS Deployment Started ====="
log "Branch: $BRANCH"
log "App Dir: $APP_DIR"

if [ -z "$REPO_URL" ] && [ -z "$DEPLOY_KEY" ]; then
    log "ERROR: AGENTS_REPO_URL or AGENTS_DEPLOY_KEY not set"
    exit 1
fi

# ===== Stop existing service =====
log "Stopping existing service..."
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
sleep 2

# ===== Setup deploy directory =====
sudo mkdir -p "$APP_DIR"
cd "$APP_DIR"

# ===== Clone or Pull =====
if [ -d ".git" ]; then
    log "Pulling latest changes..."
    sudo git pull origin "$BRANCH"
else
    log "Cloning repository..."
    if [ -n "$DEPLOY_KEY" ]; then
        GIT_URL="https://x-access-token:${DEPLOY_KEY}@${REPO_URL#https://}"
        sudo git clone --branch "$BRANCH" "$GIT_URL" "$APP_DIR"
    else
        sudo git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
    fi
fi

# ===== Ensure directory ownership =====
USER_NAME="${SUDO_USER:-$(whoami)}"
sudo chown -R "$USER_NAME:$USER_NAME" "$APP_DIR"

# ===== Install dependencies =====
log "Installing dependencies..."
cd "$APP_DIR"
python3 -m pip install --upgrade pip -q
pip install -r requirements.txt -q

# ===== Install Playwright =====
log "Installing Playwright Chromium..."
python3 -m playwright install chromium 2>/dev/null || true

# ===== Create data directories =====
mkdir -p data/artifacts data/browser_screens data/state/sandbox
chmod -R 755 data/

# ===== Start service =====
log "Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

# ===== Health check =====
sleep 5
if curl -sf http://127.0.0.1:8000/health > /dev/null; then
    log "SUCCESS: Service is running"
    echo "✅ AGENTS deployed successfully"
else
    log "WARNING: Service may not be fully running"
    journalctl -u "$SERVICE_NAME" -n 10 --no-pager
fi

log "===== Deployment Complete ====="
