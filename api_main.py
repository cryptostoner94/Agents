<<<<<<< HEAD
import os, time
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from core.agent_loop import run_agent
from core.browser_operator import extract_page, click_by_text
from core.code_sandbox import run_python
from core.shell_runner import run_shell
from core.memory import recent
 
BASE = Path("/opt/nexus-omega")
ART = BASE / "artifacts"
ART.mkdir(parents=True, exist_ok=True)
START = time.time()
app = FastAPI(title="NEXUS OMEGA", version="16.0-complete")
class ChatTask(BaseModel): message: str = ""
class BrowserTask(BaseModel): url: str; click_text: Optional[str] = None
class CodeTask(BaseModel): code: str
class ShellTask(BaseModel): command: str
HTML = r'''
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>NEXUS OMEGA</title><style>
:root{--bg:#121923;--bg2:#1b2637;--panel:rgba(28,38,55,.84);--glass:rgba(255,255,255,.075);--line:rgba(255,255,255,.12);--text:#f8fafc;--muted:#9aa7b8;--blue:#38bdf8;--violet:#8b5cf6;--green:#22c55e;--input:rgba(6,10,18,.66);--shadow:0 24px 80px rgba(0,0,0,.34)}body.light{--bg:#eef3fb;--bg2:#fff;--panel:rgba(255,255,255,.82);--glass:rgba(255,255,255,.9);--line:rgba(15,23,42,.10);--text:#0f172a;--muted:#64748b;--input:rgba(255,255,255,.92);--shadow:0 24px 70px rgba(15,23,42,.12)}*{box-sizing:border-box}html,body{height:100%}body{margin:0;color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Arial,sans-serif;background:radial-gradient(circle at 18% 6%,rgba(56,189,248,.22),transparent 28%),radial-gradient(circle at 82% 14%,rgba(139,92,246,.20),transparent 28%),linear-gradient(145deg,var(--bg),var(--bg2))}.shell{display:grid;grid-template-columns:280px 1fr;min-height:100vh;padding:18px;gap:18px}.sidebar,.main,.card,.mobile-card{border:1px solid var(--line);background:var(--panel);backdrop-filter:blur(24px);border-radius:30px;box-shadow:var(--shadow)}.sidebar{padding:18px;display:flex;flex-direction:column;gap:16px}.brand{display:flex;gap:12px;align-items:center;padding:10px 8px 18px}.orb{width:52px;height:52px;border-radius:50%;background:radial-gradient(circle,rgba(56,189,248,.9),transparent 34%),conic-gradient(#38bdf8,#8b5cf6,#22c55e,#38bdf8);box-shadow:0 0 38px rgba(56,189,248,.45)}.logo-title{font-weight:900;letter-spacing:.08em}.logo-sub{font-size:12px;color:var(--muted);letter-spacing:.28em}.nav button{width:100%;display:flex;gap:12px;padding:13px 14px;border:0;border-radius:16px;margin:4px 0;color:var(--text);background:transparent;cursor:pointer;font-weight:800;text-align:left}.nav button.active,.nav button:hover{background:linear-gradient(135deg,rgba(56,189,248,.18),rgba(139,92,246,.20))}.profile{margin-top:auto;border:1px solid var(--line);background:var(--glass);border-radius:22px;padding:14px}.mode-toggle{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px}.mode-toggle button{padding:11px;border-radius:14px;border:1px solid var(--line);background:var(--input);color:var(--text);font-weight:800}.main{overflow:hidden}.topbar{display:flex;justify-content:space-between;gap:16px;padding:22px 24px;border-bottom:1px solid var(--line)}h1{margin:0;font-size:30px}.caption{color:var(--muted);font-size:14px;margin-top:5px}.status-row{display:flex;gap:9px;flex-wrap:wrap}.chip{border:1px solid var(--line);background:var(--glass);padding:9px 12px;border-radius:999px;font-size:12px;font-weight:800}.good{color:#86efac}.content{padding:24px;display:grid;grid-template-columns:1.35fr .85fr;gap:18px}.card{padding:18px;border-radius:24px;margin-bottom:18px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}.metric{border:1px solid var(--line);background:var(--glass);border-radius:20px;padding:18px}.value{font-size:30px;font-weight:900}.timeline{position:relative;padding-left:26px}.timeline:before{content:"";position:absolute;left:8px;top:7px;bottom:7px;width:2px;background:linear-gradient(var(--blue),var(--violet),#f59e0b)}.step{position:relative;padding:13px 14px;border-radius:16px;margin-bottom:10px;background:rgba(255,255,255,.055)}.step:before{content:"";position:absolute;left:-23px;top:18px;width:12px;height:12px;border-radius:50%;background:var(--blue);box-shadow:0 0 18px var(--blue)}.step.active{background:linear-gradient(135deg,rgba(56,189,248,.16),rgba(139,92,246,.18))}.tools{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.tool{border:1px solid var(--line);background:var(--glass);border-radius:18px;padding:15px;cursor:pointer}.tool span{font-size:12px;color:var(--muted)}textarea,input{width:100%;border:1px solid var(--line);background:var(--input);color:var(--text);border-radius:18px;padding:15px;font-size:15px;margin-bottom:10px}
textarea{
height:340px;
min-height:340px;
resize:vertical;
line-height:1.5;
white-space:pre-wrap;
word-break:break-word;
overflow-wrap:anywhere;
font-size:16px
}
.primary,.secondary{border:0;border-radius:16px;padding:13px 17px;color:white;font-weight:900;cursor:pointer}.primary{background:linear-gradient(135deg,#2563eb,#8b5cf6)}.secondary{background:rgba(255,255,255,.12);border:1px solid var(--line);color:var(--text)}.output{margin-top:14px;max-height:420px;overflow:auto;white-space:pre-wrap;border:1px solid var(--line);background:rgba(3,7,18,.46);border-radius:18px;padding:16px;font-family:monospace;font-size:12px}.loader{display:none;margin-top:14px}.loader.show{display:block}.bar{height:10px;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#8b5cf6,#22c55e);animation:p 1.25s infinite}@keyframes p{0%{width:10%}50%{width:82%}100%{width:98%}}.panel{display:none}.panel.active{display:block}.mobile-shell{display:none}@media(max-width:900px){.shell{display:none}.mobile-shell{display:block;min-height:100vh;padding:env(safe-area-inset-top) 18px 18px}.mobile-top{display:flex;align-items:center;justify-content:space-between;padding:18px 0 14px}.round{width:54px;height:54px;border-radius:50%;border:1px solid var(--line);background:var(--glass);color:var(--text);display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:900}.mobile-title{text-align:center;font-weight:900}.credit-pill{border:1px solid var(--line);background:var(--glass);border-radius:999px;padding:14px 18px;font-weight:900}.mobile-card{border-radius:28px;padding:18px;margin:14px 0}.quick-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.quick{border:1px solid var(--line);background:var(--glass);border-radius:18px;padding:15px}.composer{position:fixed;left:16px;right:16px;bottom:calc(16px + env(safe-area-inset-bottom));border:1px solid var(--line);background:rgba(20,28,42,.86);backdrop-filter:blur(24px);border-radius:28px;padding:12px;box-shadow:var(--shadow)}body.light .composer{background:rgba(255,255,255,.86)}.composer-row{display:flex;gap:10px;align-items:center}
.composer input{
margin:0;
min-height:90px;
padding:18px;
font-size:16px;
line-height:1.5;
white-space:pre-wrap;
overflow-wrap:anywhere
}
.send{width:48px;height:48px;border-radius:50%;border:0;background:linear-gradient(135deg,#2563eb,#8b5cf6);color:white;font-weight:900}.mobile-output{margin-bottom:150px;white-space:pre-wrap;font-size:12px;font-family:monospace}}
</style></head><body><div class="shell"><aside class="sidebar"><div class="brand"><div class="orb"></div><div><div class="logo-title">NEXUS</div><div class="logo-sub">OMEGA</div></div></div><div class="nav"><button class="active" onclick="desktopTab('overview',this)">Overview</button><button onclick="desktopTab('agent',this)">Agent</button><button onclick="desktopTab('browser',this)">Browser Operator</button><button onclick="desktopTab('code',this)">CodeAct</button><button onclick="desktopTab('shell',this)">Safe Shell</button><button onclick="desktopTab('memory',this);memory()">Memory</button><button onclick="artifacts()">Artifacts</button><button onclick="desktopTab('settings',this)">Settings</button></div><div class="profile"><b>Operator</b><div class="caption">NEXUS OMEGA Complete</div><div class="mode-toggle"><button onclick="setTheme('dark')">Dark</button><button onclick="setTheme('light')">Light</button></div></div></aside><main class="main"><div class="topbar"><div><h1>NEXUS OMEGA Command Center</h1><div class="caption">Apple polished - cyber enhanced - autonomous execution OS</div></div><div class="status-row"><span class="chip good">VM Online</span><span class="chip good">Playwright Active</span><span class="chip">Memory Connected</span><span class="chip good">Agent Live</span></div></div><div class="content"><section><div id="overview" class="panel active"><div class="metrics"><div class="metric"><div>Tasks</div><div class="value">Live</div></div><div class="metric"><div>Browser</div><div class="value">On</div></div><div class="metric"><div>CodeAct</div><div class="value">On</div></div><div class="metric"><div>Memory</div><div class="value">On</div></div></div><div class="card"><h2>Live Execution</h2><div class="timeline"><div class="step">Planning execution</div><div class="step">Browser Operator</div><div class="step active">CodeAct</div><div class="step">Memory</div><div class="step">Artifacts</div></div></div></div><div id="agent" class="panel"><div class="card"><h2>Autonomous Agent</h2><textarea id="agent_msg">Find one AI automation opportunity that can generate revenue in 14 days and create a pilot execution plan.</textarea><button class="primary" onclick="runAgent()">Run Agent</button> <button class="secondary" onclick="loadPrompt()">Load 9.5 Prompt</button></div></div><div id="browser" class="panel"><div class="card"><h2>Browser Operator</h2><input id="browser_url" value="https://example.com"><input id="click_text" placeholder="optional click text"><button class="primary" onclick="runBrowser()">Run Browser</button></div></div><div id="code" class="panel"><div class="card"><h2>CodeAct Sandbox</h2><textarea id="code_text">print("CODEACT_OK")</textarea><button class="primary" onclick="runCode()">Run Code</button></div></div><div id="shell" class="panel"><div class="card"><h2>Safe Shell</h2><input id="shell_cmd" value="curl http://127.0.0.1:8000/health"><button class="primary" onclick="runShell()">Run Shell</button></div></div><div id="memory" class="panel"><div class="card"><h2>Persistent Memory</h2><button class="primary" onclick="memory()">Refresh Memory</button></div></div><div id="settings" class="panel"><div class="card"><h2>Settings</h2><p class="caption">Theme, shell policy, memory, Telegram and system configuration.</p></div></div><div id="loader" class="loader"><div class="bar"></div></div><pre id="out" class="output">Ready.</pre></section><aside><div class="card"><h3>Quick Actions</h3><div class="tools"><div class="tool" onclick="desktopTab('agent')"><b>Agent</b><span>Run autonomous tasks</span></div><div class="tool" onclick="desktopTab('browser')"><b>Browser</b><span>Extract data</span></div><div class="tool" onclick="desktopTab('code')"><b>CodeAct</b><span>Python sandbox</span></div><div class="tool" onclick="desktopTab('shell')"><b>Shell</b><span>Allowlisted commands</span></div></div></div><div class="card"><h3>System Health</h3><div class="step">All systems operational</div><div class="step">Memory database connected</div><div class="step">Browser automation active</div></div></aside></div></main></div><div class="mobile-shell"><div class="mobile-top"><div class="round">+</div><div class="mobile-title">NEXUS OMEGA</div><div class="credit-pill">AI</div></div><div class="mobile-card"><div class="orb" style="margin:auto"></div><h3>Quick Actions</h3><div class="quick-grid"><div class="quick" onclick="mobileFill('Find one AI automation opportunity and create a 72-hour pilot plan')"><b>Agent</b><br><span class="caption">Run task</span></div><div class="quick" onclick="mobileFill('Extract https://example.com')"><b>Browser</b><br><span class="caption">Extract web</span></div><div class="quick" onclick="mobileFill('python: print(2+2)')"><b>CodeAct</b><br><span class="caption">Run code</span></div><div class="quick" onclick="mobileFill('shell: curl http://127.0.0.1:8000/health')"><b>Shell</b><br><span class="caption">Safe command</span></div></div></div><div class="mobile-card"><h3>Task Execution</h3><div class="timeline"><div class="step">Planning execution</div><div class="step">Browser Operator</div><div class="step active">CodeAct</div><div class="step">Memory</div><div class="step">Artifacts</div></div></div><pre id="mobile_out" class="mobile-output">Ready.</pre><div class="composer"><div class="composer-row"><button class="round" style="width:48px;height:48px" onclick="memory()">+</button><textarea id="mobile_msg" placeholder="Ask NEXUS anything..." style="height:140px"></textarea><button class="send" onclick="runMobile()">^</button></div></div></div><script>let busy=false;function setTheme(t){document.body.classList.toggle("light",t==="light");localStorage.nexusTheme=t}setTheme(localStorage.nexusTheme||"dark");function desktopTab(id,btn){document.querySelectorAll(".panel").forEach(p=>p.classList.remove("active"));document.getElementById(id).classList.add("active");document.querySelectorAll(".nav button").forEach(b=>b.classList.remove("active"));if(btn)btn.classList.add("active")}function setBusy(v){busy=v;document.getElementById("loader").classList.toggle("show",v);document.querySelectorAll("button").forEach(b=>b.disabled=v)}async function post(url,data){if(busy)return;setBusy(true);try{const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});const j=await r.json();out.textContent=JSON.stringify(j,null,2);if(document.getElementById("mobile_out"))mobile_out.textContent=JSON.stringify(j,null,2)}catch(e){out.textContent=JSON.stringify({ok:false,error:e.message},null,2)}setBusy(false)}function runAgent(){post("/api/agent",{message:agent_msg.value})}function runBrowser(){post("/api/browser",{url:browser_url.value,click_text:click_text.value})}function runCode(){post("/api/code",{code:code_text.value})}function runShell(){post("/api/shell",{command:shell_cmd.value})}async function memory(){const r=await fetch("/api/memory");const j=await r.json();out.textContent=JSON.stringify(j,null,2);if(document.getElementById("mobile_out"))mobile_out.textContent=JSON.stringify(j,null,2)}async function artifacts(){const r=await fetch("/api/artifacts");out.textContent=JSON.stringify(await r.json(),null,2)}function loadPrompt(){agent_msg.value="Act as a fully autonomous AI execution company operating in 2026. Identify one real-world operational opportunity capable of generating revenue within 14 days using browser automation, APIs, AI workflows, or operational intelligence. Generate market intelligence, opportunity scoring, technical architecture, deployment strategy, automation flow, customer acquisition strategy, outreach strategy, pricing model, pilot scope, risks, screenshots, JSON artifact, markdown report, and next actions. Constraints: solo operator, under $500 infrastructure, deployable within 72 hours, real public data only, practical execution only."}function mobileFill(v){mobile_msg.value=v}function runMobile(){post("/api/agent",{message:mobile_msg.value})}</script></body></html>
'''
@app.get("/", response_class=HTMLResponse)
def root(): return HTML
@app.get("/chat", response_class=HTMLResponse)
def chat(): return HTML
@app.get("/app", response_class=HTMLResponse)
def app_page(): return HTML
@app.get("/health")
def health(): return {"ok":True,"status":"LIVE","version":"16.0-complete","uptime":int(time.time()-START)}
@app.get("/api/data")
def data(): return {"ok":True,"routes":["/chat","/api/agent","/api/browser","/api/code","/api/shell","/api/memory","/api/artifacts"]}
@app.post("/api/agent")
async def api_agent(task: ChatTask): return await run_agent(task.message)
@app.post("/api/chat")
async def api_chat(task: ChatTask): return await run_agent(task.message)
@app.post("/api/browser")
async def api_browser(task: BrowserTask):
    if task.click_text: return await click_by_text(task.url, task.click_text)
    return await extract_page(task.url)
@app.post("/api/code")
def api_code(task: CodeTask): return run_python(task.code)
@app.post("/api/shell")
def api_shell(task: ShellTask): return run_shell(task.command)
@app.get("/api/memory")
def api_memory(): return {"ok":True,"events":recent(30)}
@app.get("/api/artifacts")
def artifacts():
    files=[]
    for p in sorted(ART.glob("*"), reverse=True):
        if p.is_file(): files.append({"name":p.name,"size":p.stat().st_size,"path":str(p)})
    return {"ok":True,"files":files[:50]}
@app.get("/api/artifact/{name}")
def artifact(name: str):
    p = ART / os.path.basename(name)
    if not p.exists(): return {"ok":False,"error":"not found"}
    return FileResponse(str(p))
=======
import os
import re
import json
import time
import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT = True
except Exception:
    PLAYWRIGHT = False

BASE = "/home/cryptostoner94/nexus-omega"
ART = f"{BASE}/artifacts"
SCR = f"{BASE}/browser_screens"

os.makedirs(ART, exist_ok=True)
os.makedirs(SCR, exist_ok=True)

START = time.time()
app = FastAPI(title="NEXUS OMEGA CLEAN", version="clean-chat-final")


class Cmd(BaseModel):
    command: str = ""


class ChatTask(BaseModel):
    message: str = ""
    prompt: str = ""


class ResearchTask(BaseModel):
    goal: str = ""
    urls: Optional[List[str]] = None
    niche: str = "AI automation"
    max_urls: int = 4
    make_report: bool = True


def now():
    return datetime.now(timezone.utc).isoformat()


def clean_text(value, limit=12000):
    return re.sub(r"\s+", " ", value or "").strip()[:limit]


def extract_urls(value):
    return re.findall(r"https?://[^\s\"'<>]+", value or "")


async def extract_page(url):
    job_id = f"browser_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    screenshot = f"{SCR}/{job_id}.png"

    if not PLAYWRIGHT:
        return {"ok": False, "url": url, "error": "Playwright unavailable"}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            )
            page = await browser.new_page(viewport={"width": 1365, "height": 900})
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            try:
                await page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass

            await page.wait_for_timeout(1000)
            title = await page.title()

            try:
                text = await page.locator("body").inner_text(timeout=8000)
            except Exception:
                text = ""

            try:
                await page.screenshot(path=screenshot, full_page=True)
            except Exception:
                screenshot = None

            await browser.close()

            return {
                "ok": True,
                "id": job_id,
                "url": url,
                "status_code": response.status if response else None,
                "title": title,
                "text_preview": clean_text(text, 15000),
                "text_length": len(text or ""),
                "screenshot": screenshot,
            }

    except Exception as e:
        return {"ok": False, "id": job_id, "url": url, "error": str(e)}


async def extract_many(urls):
    return await asyncio.gather(*(extract_page(url) for url in urls))


def score_text(text):
    text = (text or "").lower()
    score = 0
    signals = []

    rules = {
        "hiring": ["hiring", "jobs", "careers"],
        "manual_work": ["manual", "spreadsheet", "admin", "workflow", "report"],
        "automation_fit": ["automation", "agent", "api", "browser", "data"],
        "revenue": ["pricing", "paid", "sales", "growth", "customer"],
    }

    for label, words in rules.items():
        if any(word in text for word in words):
            score += 2
            signals.append(label)

    return min(score, 10), signals


def build_report(goal, results):
    ranked = []

    for item in results:
        score, signals = score_text(item.get("text_preview", ""))
        ranked.append(
            {
                "source": item.get("title") or item.get("url"),
                "url": item.get("url"),
                "score": score,
                "signals": signals,
                "screenshot": item.get("screenshot"),
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)

    lines = [
        "# NEXUS OMEGA Execution Report",
        "",
        f"Generated: {now()}",
        "",
        "## Objective",
        goal,
        "",
        "## Ranked Opportunities",
        "| Rank | Source | Score | Signals | Pilot Offer |",
        "|---:|---|---:|---|---|",
    ]

    for i, row in enumerate(ranked, 1):
        lines.append(
            f"| {i} | {row['source']} | {row['score']} | {', '.join(row['signals'])} | $300-$750 72-hour pilot |"
        )

    lines += [
        "",
        "## Execution Plan",
        "- Validate the lead manually.",
        "- Offer a fixed 72-hour browser/API automation pilot.",
        "- Deliver a small working automation and report.",
        "- Convert successful pilot into recurring service.",
        "",
        "## Outreach Template",
        "Subject: Quick automation pilot",
        "",
        "Hi {{name}},",
        "",
        "I noticed signs of repetitive workflow, reporting, support, or operational work.",
        "I build small 72-hour browser/API automation pilots that reduce manual work and create usable reports.",
        "",
        "Would you be open to a short walkthrough this week?",
    ]

    return "\n".join(lines), ranked


async def run_research(goal, urls=None, max_urls=4):
    selected_urls = urls or extract_urls(goal)

    if not selected_urls:
        selected_urls = ["https://news.ycombinator.com", "https://github.com/trending"]

    selected_urls = selected_urls[:max_urls]
    results = await extract_many(selected_urls)
    markdown, ranked = build_report(goal, results)

    job_id = f"research_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    markdown_path = f"{ART}/{job_id}.md"
    json_path = f"{ART}/{job_id}.json"

    payload = {
        "ok": True,
        "id": job_id,
        "attempted_urls": selected_urls,
        "successful_extractions": sum(1 for r in results if r.get("ok")),
        "failed_extractions": sum(1 for r in results if not r.get("ok")),
        "report_path": markdown_path,
        "json_path": json_path,
        "ranked": ranked,
        "results": results,
        "preview": markdown[:2500],
    }

    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return payload


HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEXUS OMEGA CHAT</title>
<style>
:root{--bg:#070a12;--panel:#111827;--border:#263244;--input:#030712;--text:#f8fafc;--muted:#a3a3a3;--green:#22c55e;--blue:#3b82f6}
body.light{--bg:#f8fafc;--panel:#ffffff;--border:#cbd5e1;--input:#ffffff;--text:#111827;--muted:#475569}
body{margin:0;background:radial-gradient(circle at top left,#1e3a8a55,transparent 35%),var(--bg);color:var(--text);font-family:Arial}
.wrap{max-width:1150px;margin:34px auto;padding:24px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:18px;padding:22px;box-shadow:0 20px 60px rgba(0,0,0,.25)}
textarea{width:100%;height:230px;background:var(--input);color:var(--text);border:1px solid var(--border);border-radius:14px;padding:14px;font-size:16px}
button{padding:14px 20px;border:0;border-radius:12px;background:var(--green);color:white;font-weight:900;margin:10px 8px 10px 0;cursor:pointer}
button.secondary{background:var(--blue)}
button:disabled{opacity:.5;cursor:not-allowed}
pre{background:var(--input);border:1px solid var(--border);border-radius:14px;padding:16px;white-space:pre-wrap;overflow:auto;max-height:560px}
#loading{display:none;background:#1d293b;padding:12px;border-radius:12px;margin:12px 0}
.bar{height:10px;border-radius:999px;background:linear-gradient(90deg,#3b82f6,#8b5cf6,#22c55e);animation:p 1.15s infinite}
@keyframes p{0%{width:10%}50%{width:80%}100%{width:98%}}
.row{display:flex;gap:8px;flex-wrap:wrap}
.small{color:var(--muted)}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
<h1>NEXUS OMEGA CHAT COMMAND CENTER</h1>
<p class="small">Enter a normal objective, workflow, automation task, URL extraction, product-team task, or research command.</p>

<textarea id="message">Find one AI automation opportunity that can generate revenue in 14 days and create a pilot execution plan.</textarea>

<div class="row">
<button onclick="send()">Run Command</button>
<button class="secondary" onclick="health()">Health</button>
<button class="secondary" onclick="loadPrompt()">Load 9.5 Prompt</button>
<button class="secondary" onclick="theme()">Light/Dark</button>
</div>

<div id="loading"><b>Working... do not submit again until output appears.</b><div class="bar"></div></div>
<pre id="output">Ready.</pre>
</div>
</div>

<script>
let busy = false;

function setBusy(value){
  busy = value;
  document.getElementById("loading").style.display = value ? "block" : "none";
  document.querySelectorAll("button").forEach(b => b.disabled = value);
}

function theme(){
  document.body.classList.toggle("light");
  localStorage.theme = document.body.classList.contains("light") ? "light" : "dark";
}
if(localStorage.theme === "light"){document.body.classList.add("light")}

async function send(){
  if(busy) return;
  setBusy(true);
  try{
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: document.getElementById("message").value})
    });
    document.getElementById("output").textContent = JSON.stringify(await r.json(), null, 2);
  } catch(e){
    document.getElementById("output").textContent = JSON.stringify({ok:false,error:e.message}, null, 2);
  }
  setBusy(false);
}

async function health(){
  const r = await fetch("/health");
  document.getElementById("output").textContent = JSON.stringify(await r.json(), null, 2);
}

function loadPrompt(){
  document.getElementById("message").value =
    "Act as a fully autonomous AI execution company operating in 2026. Identify one real-world operational opportunity capable of generating revenue within 14 days using browser automation, APIs, AI workflows, or operational intelligence. Generate market intelligence, opportunity scoring, technical architecture, deployment strategy, automation flow, customer acquisition strategy, outreach strategy, pricing model, pilot scope, risks, screenshots, JSON artifact, and markdown report. Constraints: solo operator, under $500 infrastructure, deployable within 72 hours, real public data only, practical execution only.";
}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def root():
    return HTML


@app.get("/app", response_class=HTMLResponse)
def app_page():
    return HTML


@app.get("/chat", response_class=HTMLResponse)
def chat_page():
    return HTML


@app.get("/health")
def health():
    return {
        "ok": True,
        "status": "LIVE",
        "uptime": int(time.time() - START),
        "playwright": PLAYWRIGHT,
        "timestamp": now(),
        "version": "clean-chat-final",
    }


@app.post("/api/browser")
async def browser(cmd: Cmd):
    found_urls = extract_urls(cmd.command)

    if not found_urls:
        return {"ok": False, "error": "Missing URL", "example": "extract https://example.com"}

    results = await extract_many(found_urls[:3])
    return results[0] if len(results) == 1 else {"ok": True, "results": results}


@app.post("/api/research")
async def research(task: ResearchTask):
    return await run_research(task.goal, task.urls, task.max_urls)


@app.post("/api/product-team")
async def product_team(task: ResearchTask):
    return await run_research(task.goal, task.urls, task.max_urls)


@app.post("/api/chat")
async def chat(task: ChatTask):
    msg = (task.message or task.prompt or "").strip()
    low = msg.lower()

    if not msg:
        return {
            "ok": False,
            "error": "Missing message",
            "example": "Find one AI automation opportunity and create a pilot execution plan.",
        }

    if "health" in low or "status" in low:
        return {"ok": True, "mode": "health", "result": health()}

    found_urls = extract_urls(msg)

    if found_urls or "extract" in low or "browser" in low:
        return {
            "ok": True,
            "mode": "browser",
            "result": await browser(Cmd(command=msg)),
        }

    return {
        "ok": True,
        "mode": "agent-execution",
        "understanding": "Objective routed to research, scoring, artifact generation, and execution planning.",
        "result": await run_research(
            goal=msg,
            urls=["https://news.ycombinator.com", "https://github.com/trending"],
            max_urls=2,
        ),
    }


@app.get("/api/artifacts")
def artifacts():
    files = []

    for name in sorted(os.listdir(ART), reverse=True):
        path = f"{ART}/{name}"
        if os.path.isfile(path):
            files.append({"name": name, "size": os.path.getsize(path), "path": path})

    return {"ok": True, "count": len(files), "files": files[:50]}


@app.get("/api/artifact/{name}")
def artifact(name: str):
    path = f"{ART}/{os.path.basename(name)}"

    if not os.path.exists(path):
        return {"ok": False, "error": "not found"}

    return FileResponse(path)


@app.get("/api/data")
def data():
    return {
        "ok": True,
        "routes": [
            "/",
            "/app",
            "/chat",
            "/health",
            "/api/chat",
            "/api/browser",
            "/api/research",
            "/api/product-team",
            "/api/artifacts",
        ],
        "capabilities": [
            "chat command input",
            "browser extraction",
            "research execution",
            "product-team workflow",
            "artifact generation",
            "markdown report",
            "json report",
            "screenshots",
        ],
    }
>>>>>>> 1b2cdf6b929ec30998e89b432c04cbe093b52f38
