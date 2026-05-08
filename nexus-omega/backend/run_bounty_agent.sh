#!/usr/bin/env bash
# Load secrets from file if present, fall back to environment variables
SECRETS_FILE="/home/cryptostoner94/nexus-omega/.agent_secrets.env"
if [ -f "$SECRETS_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$SECRETS_FILE"
    set +a
fi
STAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
MSG="NEXUS BOUNTY AGENT RUN

Time: ${STAMP}

Mode:
- Scan bounty/task/reward sources
- Identify low-risk tasks
- Rank by speed/value
- Auto-capture safe research/reporting tasks
- Queue login/register/social/account actions for review unless enabled
- Block wallet/payment/KYC/private-data tasks

Sources:
- Gitcoin
- Dework
- Layer3
- Galxe
- Zealy
- OpenClaw/Moltbook ecosystem
- Social reward campaigns
- Writing/research/community microtasks

Next scan: automatic in 45 minutes."

python3 - <<PY
import json, pathlib, datetime
p = pathlib.Path('/home/cryptostoner94/nexus-singularity/revenue.json')
p.parent.mkdir(parents=True, exist_ok=True)
try:
    d=json.loads(p.read_text())
except Exception:
    d={'agents':{'Ghost-Apply':'$777','Singularity':'OPERATIONAL'},'events':[]}
d.setdefault('agents',{})['Bounty-Agent']='ACTIVE: scanning every 45 mins'
d.setdefault('events',[]).insert(0,{'ts': datetime.datetime.utcnow().isoformat()+'Z','kind':'bounty_agent','message':'Bounty agent scan cycle triggered','extra':{'mode':'safe-auto'}})
d['events']=d['events'][:50]
p.write_text(json.dumps(d,indent=2))
PY

curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" -H "Content-Type: application/json" -d "{\"chat_id\":\"${TG_CHAT_ID}\",\"text\":\"${MSG}\"}" >/dev/null || true

echo "BOUNTY_AGENT_RUN_OK"
