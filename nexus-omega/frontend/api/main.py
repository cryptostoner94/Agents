import urllib.request, urllib.error, json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse

VM = 'http://136.114.174.54:8000'
BROWSER = 'http://136.114.174.54:8010'
app = FastAPI(title='NEXUS OMEGA Proxy')


def fetch(url, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={'Content-Type': 'application/json'}
    )
    try:
        return urllib.request.urlopen(req, timeout=120).read()
    except urllib.error.URLError as e:
        raise HTTPException(status_code=502, detail=f'VM unreachable: {e.reason}')
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get('/')
def root():
    return HTMLResponse(fetch(VM + '/').decode())


@app.get('/health')
@app.get('/api/health')
def health():
    return json.loads(fetch(VM + '/health').decode())


@app.get('/api/data')
def data():
    return json.loads(fetch(VM + '/api/data').decode())


@app.get('/api/browser/status')
def browser_status():
    return json.loads(fetch(BROWSER + '/browser/status').decode())


@app.post('/api/browser/natural')
async def browser_natural(req: Request):
    body = await req.json()
    return json.loads(fetch(BROWSER + '/browser/natural', 'POST', body).decode())


# Alias used by the dashboard JS: /api/browser POST -> browser natural task
@app.post('/api/browser')
async def browser_alias(req: Request):
    body = await req.json()
    return json.loads(fetch(BROWSER + '/browser/natural', 'POST', body).decode())


@app.post('/api/exec')
async def exec_cmd(req: Request):
    body = await req.json()
    return json.loads(fetch(VM + '/api/exec', 'POST', body).decode())
