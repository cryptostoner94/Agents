import os, re, json, time, uuid, asyncio
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT=True
except Exception:
    PLAYWRIGHT=False

BASE="/home/cryptostoner94/nexus-omega"
ART=f"{BASE}/artifacts"
SCR=f"{BASE}/browser_screens"
os.makedirs(ART,exist_ok=True)
os.makedirs(SCR,exist_ok=True)

app=FastAPI(title="NEXUS OMEGA CLEAN",version="clean-final")
START=time.time()

class Cmd(BaseModel):
    command:str

class ResearchTask(BaseModel):
    goal:str
    urls:Optional[List[str]]=None
    niche:Optional[str]="AI automation"
    max_urls:int=4
    make_report:bool=True

def now():
    return datetime.now(timezone.utc).isoformat()

def urls(x):
    return re.findall(r"https?://[^\s\"'<>]+",x or "")

def clean(x,n=10000):
    return re.sub(r"\s+"," ",x or "").strip()[:n]

async def grab(url):
    jid=f"browser_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    shot=f"{SCR}/{jid}.png"
    if not PLAYWRIGHT:
        return {"ok":False,"url":url,"error":"playwright missing"}
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
            page=await b.new_page(viewport={"width":1365,"height":900})
            r=await page.goto(url,wait_until="domcontentloaded",timeout=30000)
            await page.wait_for_timeout(1200)
            title=await page.title()
            try:
                text=await page.locator("body").inner_text(timeout=8000)
            except Exception:
                text=""
            try:
                await page.screenshot(path=shot,full_page=True)
            except Exception:
                shot=None
            await b.close()
            return {"ok":True,"id":jid,"url":url,"status_code":r.status if r else None,"title":title,"text_preview":clean(text,12000),"text_length":len(text or ""),"screenshot":shot}
    except Exception as e:
        return {"ok":False,"url":url,"error":str(e)}

async def many(items):
    return await asyncio.gather(*(grab(u) for u in items))

def score(t):
    t=(t or "").lower()
    s=0; sig=[]
    rules={
      "hiring":["hiring","jobs","careers"],
      "manual_work":["manual","spreadsheet","admin","workflow","report"],
      "automation_fit":["automation","agent","api","browser","data"],
      "revenue":["pricing","paid","sales","growth"]
    }
    for k,v in rules.items():
        if any(w in t for w in v):
            s+=2; sig.append(k)
    return min(s,10),sig

HTML="""
<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1">
<title>NEXUS OMEGA CLEAN</title>
<style>
body{margin:0;background:#070a12;color:#f8fafc;font-family:Arial}
header{padding:22px;background:#111827}h1{margin:0}
main{display:grid;grid-template-columns:220px 1fr;min-height:100vh}
nav{background:#111827;padding:14px}nav div{padding:12px;cursor:pointer;color:#94a3b8;font-weight:bold}
nav div:hover,.on{background:#1d293b;color:white;border-radius:10px}
section{display:none;padding:20px}.show{display:block}
.card{background:#111827;border:1px solid #263244;border-radius:14px;padding:18px;margin-bottom:15px}
textarea,input{width:100%;background:#030712;color:white;border:1px solid #263244;border-radius:10px;padding:12px}
textarea{height:170px}button{background:#22c55e;color:white;border:0;border-radius:10px;padding:11px 15px;margin:8px;font-weight:bold}
pre{background:#030712;border:1px solid #263244;border-radius:12px;padding:14px;white-space:pre-wrap;overflow:auto;max-height:520px}
#bar{display:none;background:#020617;padding:10px}
</style></head><body>
<header><h1>NEXUS OMEGA CLEAN</h1><p>Working dashboard: health, browser, research, product team, crypto workbench, artifacts.</p></header>
<div id=bar>Working... wait until output appears.</div>
<main><nav>
<div class=on onclick="tab('d',this)">Dashboard</div>
<div onclick="tab('b',this)">Browser</div>
<div onclick="tab('r',this)">Research</div>
<div onclick="tab('p',this)">Product Team</div>
<div onclick="tab('w',this)">Crypto Workbench</div>
<div onclick="tab('a',this)">Artifacts</div>
</nav><div>
<section id=d class=show><div class=card><button onclick=health()>Health</button><button onclick=data()>Capabilities</button><pre id=dout></pre></div></section>
<section id=b><div class=card><h2>Browser</h2><textarea id=bcmd>extract https://example.com</textarea><button onclick=browserRun()>Run</button><pre id=bout></pre></div></section>
<section id=r><div class=card><h2>Research</h2><textarea id=rgoal>Act as a real AI execution company. Find operational automation opportunities capable of generating revenue within 14 days.</textarea><button onclick=researchRun()>Run</button><pre id=rout></pre></div></section>
<section id=p><div class=card><h2>Product Team</h2><textarea id=pgoal>Find one urgent operational pain point, design an MVP, estimate pricing, create outreach copy, and recommend fastest path to first $1000 revenue.</textarea><button onclick=productRun()>Run</button><pre id=pout></pre></div></section>
<section id=w><div class=card><h2>Crypto Workbench</h2><input id=wallet placeholder="wallet/explorer URL/note"><button onclick=saveWallet()>Save</button><button onclick=walletRun()>Run Intelligence</button><pre id=wout></pre></div></section>
<section id=a><div class=card><h2>Artifacts</h2><button onclick=artifacts()>List</button><pre id=aout></pre></div></section>
</div></main>
<script>
let wallets=JSON.parse(localStorage.wallets||"[]");
function tab(id,e){document.querySelectorAll("section").forEach(x=>x.classList.remove("show"));document.querySelectorAll("nav div").forEach(x=>x.classList.remove("on"));document.getElementById(id).classList.add("show");e.classList.add("on")}
function show(id,x){document.getElementById(id).textContent=JSON.stringify(x,null,2)}
async function run(id,fn){bar.style.display="block";try{show(id,await fn())}catch(e){show(id,{ok:false,error:e.message})}bar.style.display="none"}
async function health(){run("dout",async()=>await(await fetch("/health")).json())}
async function data(){run("dout",async()=>await(await fetch("/api/data")).json())}
async function browserRun(){run("bout",async()=>await(await fetch("/api/browser",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({command:bcmd.value})})).json())}
async function researchRun(){run("rout",async()=>await(await fetch("/api/research",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({goal:rgoal.value,urls:["https://news.ycombinator.com","https://github.com/trending"],max_urls:2,make_report:true})})).json())}
async function productRun(){run("pout",async()=>await(await fetch("/api/product-team",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({goal:pgoal.value,urls:["https://news.ycombinator.com","https://github.com/trending"],max_urls:2,make_report:true})})).json())}
function saveWallet(){wallets.push(wallet.value);localStorage.wallets=JSON.stringify(wallets);show("wout",{ok:true,wallets})}
async function walletRun(){let u=wallets.filter(x=>x.startsWith("http"));if(!u.length){show("wout",{ok:true,message:"Saved locally. Add explorer URL for extraction.",wallets});return}run("wout",async()=>await(await fetch("/api/research",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({goal:"Crypto workbench: "+JSON.stringify(wallets),urls:u,max_urls:4})})).json())}
async function artifacts(){run("aout",async()=>await(await fetch("/api/artifacts")).json())}
health();
</script></body></html>
"""

@app.get("/",response_class=HTMLResponse)
def root(): return HTML

@app.get("/app",response_class=HTMLResponse)
def ui(): return HTML

@app.get("/health")
def health():
    return {"ok":True,"status":"LIVE","uptime":int(time.time()-START),"playwright":PLAYWRIGHT,"timestamp":now(),"version":"clean-final"}

@app.get("/api/data")
def data():
    return {"ok":True,"routes":["/","/app","/health","/api/browser","/api/research","/api/product-team","/api/artifacts"],"capabilities":["browser extraction","research reports","product-team workflow","crypto workbench","artifacts"]}

@app.post("/api/browser")
async def browser(c:Cmd):
    u=urls(c.command)
    if not u: return {"ok":False,"example":"extract https://example.com"}
    r=await many(u[:3])
    return r[0] if len(r)==1 else {"ok":True,"results":r}

@app.post("/api/research")
async def research(t:ResearchTask):
    u=(t.urls or urls(t.goal) or ["https://news.ycombinator.com"])[:t.max_urls]
    results=await many(u)
    rows=[]
    for r in results:
        sc,sig=score(r.get("text_preview",""))
        rows.append({"source":r.get("title") or r.get("url"),"url":r.get("url"),"score":sc,"signals":sig,"screenshot":r.get("screenshot")})
    md="# NEXUS OMEGA REPORT\\n\\nGoal: "+t.goal+"\\n\\n"+json.dumps(rows,indent=2)
    jid=f"research_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    mp=f"{ART}/{jid}.md"; jp=f"{ART}/{jid}.json"
    payload={"ok":True,"id":jid,"attempted_urls":u,"successful_extractions":sum(1 for r in results if r.get("ok")),"failed_extractions":sum(1 for r in results if not r.get("ok")),"report_path":mp,"json_path":jp,"ranked":rows,"results":results,"preview":md[:2000]}
    open(mp,"w").write(md)
    open(jp,"w").write(json.dumps(payload,indent=2))
    return payload

@app.post("/api/product-team")
async def product(t:ResearchTask):
    return await research(t)

@app.get("/api/artifacts")
def artifacts():
    files=[{"name":n,"path":f"{ART}/{n}","size":os.path.getsize(f"{ART}/{n}")} for n in sorted(os.listdir(ART),reverse=True) if os.path.isfile(f"{ART}/{n}")]
    return {"ok":True,"count":len(files),"files":files[:50]}

@app.get("/api/artifact/{name}")
def artifact(name:str):
    p=f"{ART}/{os.path.basename(name)}"
    return FileResponse(p) if os.path.exists(p) else {"ok":False,"error":"not found"}
