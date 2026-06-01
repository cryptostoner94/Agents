# AGENTS - AWS EC2 + GitHub Auto-Deploy Setup Guide

This guide explains how to set up automatic deployment from GitHub to AWS EC2.

## Architecture

```
GitHub Push → GitHub Webhook → EC2 Webhook Server → Git Pull → Service Restart
```

## Prerequisites

1. **AWS EC2 Instance** (Ubuntu 20.04+)
   - Security group: ports 22 (SSH), 8000 (app), 8443 (webhook) open
   - SSH key pair configured

2. **GitHub Repository** named `Agents` with the application code

3. **GitHub Personal Access Token** (for private repos)
   - Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - Permissions: Repository access (select your repo)

## Step 1: EC2 Initial Setup

SSH into your EC2 instance and run:

```bash
# Clone the repo (public) or use deploy key (private)
git clone https://github.com/youruser/Agents.git /opt/Agents
cd /opt/Agents

# Run setup
chmod +x deploy/setup-ec2.sh
sudo bash deploy/setup-ec2.sh
```

Or manually:

```bash
# Install dependencies
sudo apt-get update && sudo apt-get install -y python3 python3-pip git curl
pip3 install fastapi uvicorn pydantic playwright requests httpx

# Install Playwright browser
python3 -m playwright install chromium

# Copy systemd service
sudo cp deploy/Agents.service /etc/systemd/system/
sudo cp deploy/nexus-webhook.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable Agents nexus-webhook

# Create .env file with your API keys
cp .env.template .env
nano .env  # Add your keys
```

## Step 2: Configure GitHub Webhook

1. Go to your GitHub repo → Settings → Webhooks → Add webhook

2. Configure:
   - **Payload URL**: `https://YOUR_EC2_IP:8443/webhook`
   - **Content type**: `application/json`
   - **Secret**: Your webhook secret (match with `NEXUS_WEBHOOK_SECRET`)
   - **Events**: Just `push` events

3. For HTTPS (recommended):
   ```bash
   # Install nginx and certbot
   sudo apt-get install -y nginx certbot python3-certbot-nginx
   
   # Get SSL certificate
   sudo certbot --nginx -d yourdomain.com
   
   # Configure nginx to proxy to webhook server
   sudo nano /etc/nginx/sites-available/default
   ```

## Step 3: Using GitHub Actions (Alternative)

If you prefer GitHub Actions over webhooks:

1. Add these secrets to your GitHub repo:
   - `EC2_HOST`: Your EC2 public IP
   - `EC2_USER`: ubuntu (or your user)
   - `EC2_SSH_KEY`: Your private SSH key

2. The workflow file is at `deploy/github-actions-deploy.yml`

3. It will:
   - Sync files on push to main
   - SSH into EC2
   - Install dependencies
   - Restart the service
   - Run health check

## Step 4: Environment Configuration

Create `/opt/Agents/.env`:

```bash
# Server
NEXUS_BASE=/opt/Agents/data
PORT=8000

# LLM (for AI reasoning)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# GitHub Auto-Deploy
NEXUS_DEPLOY_KEY=ghp_...
NEXUS_REPO_URL=https://github.com/youruser/Agents.git
NEXUS_BRANCH=main
NEXUS_WEBHOOK_SECRET=your-secret

# Telegram (optional)
TG_TOKEN=...
```

## Step 5: Start Services

```bash
# Start the app
sudo systemctl start Agents

# Start the webhook server
sudo systemctl start nexus-webhook

# Check status
sudo systemctl status Agents
curl http://127.0.0.1:8000/health
```

## Deployment Workflow

### Option A: Webhook (Recommended for real-time)

1. You push to GitHub
2. GitHub sends webhook to EC2
3. `webhook_server.py` receives the push event
4. It triggers `github-auto-deploy.sh`
5. Script pulls latest code, installs dependencies, restarts service

### Option B: GitHub Actions (Recommended for reliability)

1. You push to GitHub
2. GitHub Actions workflow triggers
3. Actions syncs files to EC2 via rsync
4. Actions SSH into EC2 and restarts service

## Monitoring

```bash
# View service logs
sudo journalctl -u Agents -f

# View webhook logs
sudo journalctl -u nexus-webhook -f

# View deployment logs
tail -f /var/log/nexus-deploy.log

# Health check
curl http://127.0.0.1:8000/health
```

## Troubleshooting

### Webhook not working?
```bash
# Check if webhook server is running
sudo systemctl status nexus-webhook

# Check firewall
sudo ufw status
sudo ufw allow 8443/tcp

# Test webhook manually
curl -X POST https://your-ec2:8443/webhook -d '{}' -H "Content-Type: application/json"
```

### Deployment failing?
```bash
# Check deployment script logs
cat /var/log/nexus-deploy.log

# Verify SSH connectivity
ssh -i key.pem ubuntu@ec2-ip

# Check git repo
cd /opt/Agents && git status
```

### App not starting?
```bash
# Check syntax
python3 -m py_compile api_main.py

# Check dependencies
pip install -r requirements.txt

# Manual start for debugging
cd /opt/Agents
python3 -m uvicorn api_main:app --host 0.0.0.0 --port 8000
```

## Production Checklist

- [ ] SSL certificate configured (HTTPS)
- [ ] Firewall rules set
- [ ] `.env` file with real keys
- [ ] GitHub webhook or Actions configured
- [ ] Health checks passing
- [ ] Logs being monitored
- [ ] Backup strategy for data directory
- [ ] Monitoring/alerting set up (optional)