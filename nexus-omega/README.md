# NEXUS OMEGA

Persistent VM-backed agent control system with Telegram commands, browser automation,
bounty/task workflow support, Vercel frontend proxy, and Playwright browser execution.

## Live Architecture

| Layer | Where |
|---|---|
| Frontend / Mini App | Vercel — https://nexusomegaverceldeploy.vercel.app |
| Backend API | GCP VM — http://136.114.174.54:8000 |
| Browser API | GCP VM — http://136.114.174.54:8010 |
| Telegram Bot | https://t.me/CompleteAgent_bot |
| Persistence | systemd services + JSON state on VM |

## Services

```
nexus-omega.service          — FastAPI backend on :8000
nexus-tg-poller.service      — Telegram long-polling bot
nexus-browser-api.service    — Playwright browser API on :8010
nexus-bounty-agent.timer     — Bounty agent every 45 minutes
```

## VM Access

```bash
gcloud compute ssh agents-ai-prod --zone=us-central1-a --project=gen-lang-client-0416088592
```

## Fresh VM Setup (Cloud Shell — one block)

```bash
set -e
REPO=https://github.com/cryptostoner94/Agents
APP=/home/cryptostoner94/nexus-omega

git clone $REPO /tmp/nexus-src
mkdir -p $APP
cp -r /tmp/nexus-src/Agents/nexus-omega/. $APP/

cd $APP
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
playwright install chromium --with-deps

cp backend/.env.example .agent_secrets.env
nano .agent_secrets.env

sudo cp backend/systemd/*.service /etc/systemd/system/
sudo cp backend/systemd/*.timer   /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nexus-omega nexus-tg-poller nexus-browser-api nexus-bounty-agent.timer
```

## Health Checks

```bash
curl http://127.0.0.1:8000/health
curl http://136.114.174.54:8000/health
curl http://127.0.0.1:8010/browser/status
```

## Telegram Commands

```
/start                   Welcome + full command list
/commands                Full command list
/status                  Live agent status
/set <agent> <val>       Update agent value

/browser_help            Browser agent command list
/browser_extract <url>   Extract title + text from URL
/browser_apply <url>     Apply workflow on URL
/browser_register <url>  Register workflow on URL
/browser_status          Last browser run state

/bounty_now              Run bounty agent immediately
/start_bounty_agent      Alias for /bounty_now
/bounty_status           Current bounty agent status
/agent_policy            Show safety policy
```

## Vercel Deploy

```bash
cd frontend
vercel --prod
```

## GitHub Push

```bash
git add -A
git commit -m "fix: QA pass — harden services, fix proxy, add systemd units"
git push origin main
```

## Secrets

Never commit secrets. Use:
  /home/cryptostoner94/nexus-omega/.agent_secrets.env

Template: backend/.env.example
