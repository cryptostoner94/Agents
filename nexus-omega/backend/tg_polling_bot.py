import os, time, json, urllib.parse, urllib.request, subprocess
from pathlib import Path

APP=Path('/home/cryptostoner94/nexus-omega')
DATA=Path('/home/cryptostoner94/nexus-singularity/revenue.json')
SECRETS=APP/'.agent_secrets.env'

def read_env():
    e={}
    if SECRETS.exists():
        for line in SECRETS.read_text().splitlines():
            if '=' in line and not line.strip().startswith('#'):
                k,v=line.split('=',1); e[k.strip()]=v.strip().strip('"').strip("'")
    return e

ENV=read_env()
TG_TOKEN=ENV.get('TG_TOKEN') or os.getenv('TG_TOKEN')

def api(method,payload=None):
    data=urllib.parse.urlencode(payload or {}).encode()
    return json.loads(urllib.request.urlopen(f'https://api.telegram.org/bot{TG_TOKEN}/{method}',data=data,timeout=60).read())

def reply(cid,text):
    api('sendMessage',{'chat_id':cid,'text':text[:3900]})

def run(cmd):
    return subprocess.check_output(cmd,shell=True,cwd=str(APP),stderr=subprocess.STDOUT,timeout=90).decode()[-3000:]

def store():
    if not DATA.exists():
        DATA.parent.mkdir(parents=True,exist_ok=True)
        DATA.write_text(json.dumps({'agents':{'Ghost-Apply':'$777','Singularity':'OPERATIONAL'},'events':[]},indent=2))
    return json.loads(DATA.read_text())

def save(d): DATA.write_text(json.dumps(d,indent=2))

def handle(msg):
    cid=(msg.get('chat') or {}).get('id')
    text=(msg.get('text') or '').strip()
    if not cid: return
    d=store(); agents=d.setdefault('agents',{})
    if text in ['/start', '/help', '/commands']:
        reply(cid, (
            'NEXUS OMEGA LIVE\n\n'
            'Core:\n/status\n/set <agent> <value>\n\n'
            'Browser:\n/browser_help\n/browser_extract https://example.com\n/browser_status\n\n'
            'Bounty:\n/bounty_now\n/start_bounty_agent\n/bounty_status\n/agent_policy'
        ))
    elif text == '/status':
        reply(cid,'NEXUS STATUS: LIVE\n'+'\n'.join([f'{k}: {v}' for k,v in agents.items()]))
    elif text.startswith('/set '):
        p=text.split(' ',2)
        if len(p)==3:
            agents[p[1]]=p[2]; save(d); reply(cid,f'Updated {p[1]} = {p[2]}')
        else: reply(cid,'Usage: /set Ghost-Apply $1000')
    elif text=='/browser_help':
        reply(cid,'Browser Agent Commands:\n/browser_extract <url>\n/browser_apply <url>\n/browser_register <url>\n/browser_status')
    elif text=='/browser_status':
        reply(cid,run('./run_browser_agent.sh status'))
    elif text.startswith('/browser_extract '):
        url=text.split(' ',1)[1].strip(); reply(cid,run(f'./run_browser_agent.sh natural "extract {url}"'))
    elif text.startswith('/browser_apply '):
        url=text.split(' ',1)[1].strip(); reply(cid,run(f'./run_browser_agent.sh natural "apply {url}"'))
    elif text.startswith('/browser_register '):
        url=text.split(' ',1)[1].strip(); reply(cid,run(f'./run_browser_agent.sh natural "register {url}"'))
    elif text == '/bounty_now' or text == '/start_bounty_agent':
        reply(cid, run('./run_bounty_agent.sh || true'))
    elif text=='/bounty_status':
        reply(cid,agents.get('Bounty-Agent','Bounty agent pending or active'))
    elif text=='/agent_policy':
        reply(cid,'Auto: scan, rank, summarize, draft, report, low-risk no-money tasks. Review/block: wallet, payment, KYC, private keys, capital handling, captcha.')
    else:
        reply(cid,'Unknown command. Use /commands')

def main():
    if not TG_TOKEN:
        print('FATAL: TG_TOKEN is not set. Export TG_TOKEN or add it to .agent_secrets.env', flush=True)
        raise SystemExit(1)
    try: api('deleteWebhook', {'drop_pending_updates': 'true'})
    except Exception: pass
    offset = 0
    while True:
        try:
            u = api('getUpdates', {'timeout': 50, 'offset': offset})
            for x in u.get('result', []):
                offset = max(offset, x['update_id'] + 1)
                m = x.get('message') or x.get('edited_message')
                if m:
                    handle(m)
        except Exception as e:
            print('poll_error', e, flush=True)
            time.sleep(5)

if __name__=='__main__': main()
