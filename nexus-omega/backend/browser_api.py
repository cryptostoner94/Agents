from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
from pathlib import Path

APP = Path('/home/cryptostoner94/nexus-omega')
app = FastAPI(title='NEXUS Browser API')

class Cmd(BaseModel):
    command: str

@app.get('/browser/status')
def status():
    p = subprocess.run(['./run_browser_agent.sh', 'status'], cwd=str(APP), capture_output=True, text=True, timeout=60)
    return {'code': p.returncode, 'stdout': p.stdout[-12000:], 'stderr': p.stderr[-12000:]}

@app.post('/browser/natural')
def natural(c: Cmd):
    p = subprocess.run(['./run_browser_agent.sh', 'natural', c.command], cwd=str(APP), capture_output=True, text=True, timeout=180)
    return {'code': p.returncode, 'stdout': p.stdout[-12000:], 'stderr': p.stderr[-12000:]}
