from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json, time, subprocess

APP = Path('/home/cryptostoner94/nexus-omega')
DATA = Path('/home/cryptostoner94/nexus-singularity')
REVENUE = DATA / 'revenue.json'
START = time.time()

app = FastAPI(title='NEXUS OMEGA')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

class Cmd(BaseModel):
    command: str

def load():
    DATA.mkdir(parents=True, exist_ok=True)
    if not REVENUE.exists():
        REVENUE.write_text(json.dumps({
            'agents': {
                'Ghost-Apply': '$777',
                'Browser-Agent': 'READY',
                'Bounty-Agent': 'ACTIVE',
                'Singularity': 'OPERATIONAL'
            },
            'events': []
        }, indent=2))
    return json.loads(REVENUE.read_text())

@app.get('/')
def root():
    return HTMLResponse('''
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"/><title>NEXUS OMEGA</title>
<style>
body{margin:0;background:#070812;color:white;font-family:system-ui}main{max-width:1100px;margin:auto;padding:18px}.card{background:#141722;border:1px solid #303447;border-radius:24px;padding:18px;margin:14px 0}button,input,textarea{width:100%;box-sizing:border-box;padding:14px;border-radius:14px;margin:7px 0;background:#05060b;color:white;border:1px solid #333}button{background:#315cff;font-weight:800}pre{white-space:pre-wrap;background:#05060b;padding:14px;border-radius:14px;overflow:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}</style></head>
<body><main><h1>NEXUS OMEGA CONTROL GRID</h1><div class="grid"><div class="card"><h2>Live Data</h2><pre id="data"></pre></div><div class="card"><h2>VM Console</h2><textarea id="cmd">pwd && ls -la</textarea><button onclick="execCmd()">Execute</button><pre id="out"></pre></div><div class="card"><h2>Browser Agent</h2><textarea id="task">extract https://example.com</textarea><button onclick="browserTask()">Run Browser Task</button><pre id="bout"></pre></div></div></main>
<script>
async function load(){data.textContent=JSON.stringify(await fetch('/api/data').then(r=>r.json()),null,2)}
async function execCmd(){out.textContent=JSON.stringify(await fetch('/api/exec',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:cmd.value})}).then(r=>r.json()),null,2);load()}
async function browserTask(){bout.textContent=JSON.stringify(await fetch('/api/browser',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:task.value})}).then(r=>r.json()),null,2);load()}
load();setInterval(load,10000)
</script></body></html>''')

@app.get('/health')
@app.get('/api/health')
def health():
    return {'ok': True, 'status': 'LIVE', 'uptime': int(time.time() - START)}

@app.get('/api/data')
def data():
    d = load()
    return {
        'ok': True,
        'status': 'LIVE',
        'agents': d.get('agents', {}),
        'events': d.get('events', [])[:30],
        'services': {
            'nexus-omega': subprocess.getoutput('systemctl is-active nexus-omega || true'),
            'nexus-tg-poller': subprocess.getoutput('systemctl is-active nexus-tg-poller || true'),
            'nexus-browser-api': subprocess.getoutput('systemctl is-active nexus-browser-api || true')
        }
    }

@app.post('/api/exec')
def exec_cmd(c: Cmd):
    blocked = ['rm -rf /', 'mkfs', 'shutdown', 'reboot', 'dd if=', ':(){']
    if any(x in c.command for x in blocked):
        raise HTTPException(400, 'blocked destructive command')
    p = subprocess.run(c.command, shell=True, cwd=str(APP), capture_output=True, text=True, timeout=60)
    return {'code': p.returncode, 'stdout': p.stdout[-10000:], 'stderr': p.stderr[-10000:]}

@app.post('/api/browser')
def browser_cmd(c: Cmd):
    p = subprocess.run(['/home/cryptostoner94/nexus-omega/run_browser_agent.sh', 'natural', c.command], cwd=str(APP), capture_output=True, text=True, timeout=180)
    return {'code': p.returncode, 'stdout': p.stdout[-12000:], 'stderr': p.stderr[-12000:]}
