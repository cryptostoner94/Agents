# NEXUS OMEGA — Operations Runbook

## Start / restart all services

```bash
sudo systemctl restart nexus-omega
sudo systemctl restart nexus-tg-poller
sudo systemctl restart nexus-browser-api
sudo systemctl restart nexus-bounty-agent.timer
```

## Enable services on boot

```bash
sudo systemctl enable nexus-omega nexus-tg-poller nexus-browser-api nexus-bounty-agent.timer
```

## Service status

```bash
sudo systemctl status nexus-omega
sudo systemctl status nexus-tg-poller
sudo systemctl status nexus-browser-api
sudo systemctl list-timers nexus-bounty-agent.timer
```

## Logs

```bash
journalctl -u nexus-omega          -n 100 --no-pager
journalctl -u nexus-tg-poller      -n 100 --no-pager
journalctl -u nexus-browser-api    -n 100 --no-pager
journalctl -u nexus-bounty-agent   -n 100 --no-pager
```

## Browser Agent Manual Test

```bash
cd ~/nexus-omega
./backend/run_browser_agent.sh natural "extract https://example.com"
```

## Browser API Manual Test

```bash
curl http://127.0.0.1:8010/browser/status
curl -X POST http://127.0.0.1:8010/browser/natural \
  -H 'Content-Type: application/json' \
  -d '{"command":"extract https://example.com"}'
```

## Backend API Manual Test

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/data
curl -X POST http://127.0.0.1:8000/api/exec \
  -H 'Content-Type: application/json' \
  -d '{"command":"uptime"}'
```

## Bounty Agent Manual Trigger

```bash
cd ~/nexus-omega
bash backend/run_bounty_agent.sh
```

## Install systemd units (after repo update)

```bash
sudo cp ~/nexus-omega/backend/systemd/*.service /etc/systemd/system/
sudo cp ~/nexus-omega/backend/systemd/*.timer   /etc/systemd/system/
sudo systemctl daemon-reload
```

## Vercel Deploy

```bash
cd ~/nexus-omega/frontend
vercel --prod
```

## GitHub Push

```bash
cd ~/nexus-omega
git add -A
git commit -m "chore: update"
git push origin main
```
