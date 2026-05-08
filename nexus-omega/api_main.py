import os
import re
import json
import time
import uuid
import asyncio
import traceback
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

try:
    from fastapi.middleware.cors import CORSMiddleware
except Exception:
    CORSMiddleware = None

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False

BASE_DIR = "/home/cryptostoner94/nexus-omega"
ARTIFACT_DIR = os.path.join(BASE_DIR, "artifacts")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "browser_screens")

os.makedirs(ARTIFACT_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

START_TIME = time.time()

app = FastAPI(title="NEXUS OMEGA Execution Grade", version="10.2-execution")

if CORSMiddleware:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

class Cmd(BaseModel):
    command: str

class ResearchTask(BaseModel):
    goal: str
    urls: Optional[List[str]] = None
    niche: Optional[str] = "AI automation"
    max_urls: int = 4
    make_report: bool = True

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def clean_text(text: str, limit: int = 12000):
    return re.sub(r"\s+", " ", text or "").strip()[:limit]

def extract_urls(text: str):
    return re.findall(r"https?://[^\s\"'<>]+", text or "")

async def extract_page(url: str) -> Dict[str, Any]:
    job_id = f"browser_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{job_id}.png")

    if not PLAYWRIGHT_AVAILABLE:
        return {"ok": False, "url": url, "error": "Playwright unavailable"}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            )
            page = await browser.new_page(
                viewport={"width": 1365, "height": 900},
                user_agent="Mozilla/5.0 Chrome/122 Safari/537.36",
            )

            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            await page.wait_for_timeout(1500)

            title = await page.title()

            try:
                body = await page.locator("body").inner_text(timeout=10000)
            except Exception:
                body = ""

            try:
                await page.screenshot(path=screenshot_path, full_page=True)
            except Exception:
                screenshot_path = None

            await browser.close()

            return {
                "ok": True,
                "id": job_id,
                "url": url,
                "status_code": response.status if response else None,
                "title": title,
                "text_preview": clean_text(body, 15000),
                "text_length": len(body or ""),
                "screenshot": screenshot_path,
            }

    except Exception as e:
        return {
            "ok": False,
            "id": job_id,
            "url": url,
            "error": str(e),
            "trace": traceback.format_exc()[-2000:],
        }

async def extract_many(urls: List[str], concurrency: int = 2):
    sem = asyncio.Semaphore(concurrency)

    async def run_one(url):
        async with sem:
            return await extract_page(url)

    return await asyncio.gather(*(run_one(u) for u in urls))

def score_text(text: str):
    t = (text or "").lower()
    score = 0
    signals = []

    checks = {
        "hiring": ["hiring", "jobs", "careers", "support", "operations", "engineer"],
        "manual_work": ["manual", "spreadsheet", "admin", "email", "workflow", "report"],
        "automation_fit": ["automation", "agent", "api", "browser", "scrape", "data"],
        "buyer_pain": ["slow", "delay", "cost", "customer", "scale", "repetitive"],
        "revenue": ["pricing", "paid", "subscription", "sales", "growth", "client"],
    }

    for label, words in checks.items():
        if any(w in t for w in words):
            score += 2
            signals.append(label)

    return min(score, 10), signals

def build_report(goal: str, niche: str, results: List[Dict[str, Any]]):
    ranked = []

    for r in results:
        score, signals = score_text(r.get("text_preview", ""))
        ranked.append({
            "source": r.get("title") or r.get("url"),
            "url": r.get("url"),
            "ok": r.get("ok"),
            "score": score,
            "signals": signals,
            "screenshot": r.get("screenshot"),
            "pilot_offer": "72-hour automation audit + prototype",
            "price_range": "$300-$750 pilot",
            "next_action": "Verify buyer/contact path and send targeted pilot offer",
            "preview": clean_text(r.get("text_preview", ""), 1200),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)

    lines = []
    lines.append("# NEXUS OMEGA End-to-End Execution Report")
    lines.append("")
    lines.append(f"Generated: {now_iso()}")
    lines.append("")
    lines.append("## Mission")
    lines.append(goal)
    lines.append("")
    lines.append("## Niche")
    lines.append(niche)
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(f"- Sources attempted: {len(results)}")
    lines.append(f"- Successful extractions: {sum(1 for r in results if r.get('ok'))}")
    lines.append(f"- Failed extractions: {sum(1 for r in results if not r.get('ok'))}")
    lines.append("- Generated browser screenshots, markdown report, JSON dataset, scoring, and outreach strategy.")
    lines.append("")
    lines.append("## Ranked Opportunities")
    lines.append("")
    lines.append("| Rank | Source | Score | Signals | Pilot Offer | Price |")
    lines.append("|---:|---|---:|---|---|---|")

    for i, row in enumerate(ranked, 1):
        lines.append(f"| {i} | {row['source']} | {row['score']} | {', '.join(row['signals'])} | {row['pilot_offer']} | {row['price_range']} |")

    lines.append("")
    lines.append("## Top Actions")

    for i, row in enumerate(ranked[:3], 1):
        lines.append("")
        lines.append(f"### {i}. {row['source']}")
        lines.append(f"- URL: {row['url']}")
        lines.append(f"- Score: {row['score']}/10")
        lines.append(f"- Signals: {', '.join(row['signals'])}")
        lines.append(f"- Screenshot: `{row['screenshot']}`")
        lines.append("- Offer: fixed pilot to automate repetitive browser/API/reporting work.")
        lines.append("- Pricing: $300-$750 for a 72-hour pilot.")
        lines.append("- Follow-up: manually verify contact path, then send targeted outreach.")
        lines.append("")
        lines.append("Preview:")
        lines.append("```text")
        lines.append(row["preview"])
        lines.append("```")

    lines.append("")
    lines.append("## Cold Outreach Template")
    lines.append("")
    lines.append("Subject: Quick automation pilot for your operations workflow")
    lines.append("")
    lines.append("Hi {{name}},")
    lines.append("")
    lines.append("I noticed signals that your team may be handling repetitive admin, reporting, support, or workflow tasks manually.")
    lines.append("")
    lines.append("I build lightweight browser/API automation pilots that reduce manual work and create usable reports or workflows within 72 hours.")
    lines.append("")
    lines.append("Would you be open to a short walkthrough this week?")
    lines.append("")
    lines.append("Best,")
    lines.append("{{your_name}}")
    lines.append("")
    lines.append("## Caveat")
    lines.append("This produces operational intelligence and execution artifacts. Revenue is not guaranteed; manual validation is required.")

    return "\n".join(lines), ranked

APP_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEXUS OMEGA</title>
<style>
body{margin:0;background:#0d1117;color:#f0f6fc;font-family:Arial}
header{background:#161b22;padding:18px;border-bottom:1px solid #30363d}
.tabs{display:flex;flex-wrap:wrap;background:#11161c;border-bottom:1px solid #30363d}
.tab{padding:13px 16px;cursor:pointer;border-right:1px solid #30363d}
.tab:hover{background:#1b2330}
.panel{display:none;padding:20px}
.active{display:block}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:18px;margin-bottom:18px}
textarea{width:100%;height:180px;background:#010409;color:#58ffb3;border:1px solid #30363d;border-radius:8px;padding:12px}
button{padding:12px 18px;background:#238636;color:white;border:0;border-radius:8px;cursor:pointer;margin:8px 8px 8px 0}
pre{background:#010409;color:#d1f7d6;border:1px solid #30363d;border-radius:8px;padding:14px;white-space:pre-wrap;overflow:auto;max-height:520px}
.small{color:#9da7b3}
</style>
</head>
<body>
<header>
<h1>NEXUS OMEGA 10.2</h1>
<div class="small">Execution-grade browser research, product-team workflow, artifacts, and reports</div>
</header>

<div class="tabs">
<div class="tab" onclick="showTab('dash')">Dashboard</div>
<div class="tab" onclick="showTab('browser')">Browser</div>
<div class="tab" onclick="showTab('research')">Research</div>
<div class="tab" onclick="showTab('product')">Product Team</div>
<div class="tab" onclick="showTab('risk')">Passive Risk Review</div>
<div class="tab" onclick="showTab('artifacts')">Artifacts</div>
</div>

<div id="dash" class="panel active">
<div class="card">
<h2>Health</h2>
<button onclick="health()">Check Health</button>
<button onclick="capabilities()">Capabilities</button>
<pre id="dashOut">Ready.</pre>
</div>
</div>

<div id="browser" class="panel">
<div class="card">
<h2>Browser Agent</h2>
<textarea id="browserCmd">extract https://example.com</textarea>
<button onclick="browserRun()">Run Browser</button>
<pre id="browserOut"></pre>
</div>
</div>

<div id="research" class="panel">
<div class="card">
<h2>Research Agent</h2>
<textarea id="researchGoal">Act as a real AI execution company. Find operational automation opportunities capable of generating revenue within 14 days.</textarea>
<button onclick="researchRun()">Run Research</button>
<pre id="researchOut"></pre>
</div>
</div>

<div id="product" class="panel">
<div class="card">
<h2>Product Team</h2>
<textarea id="productGoal">Act as a fully autonomous product and revenue team. Identify one real-world operational opportunity, score it, create a pilot offer, technical implementation plan, outreach strategy, pricing, and execution roadmap.</textarea>
<button onclick="productRun()">Run Product Team</button>
<pre id="productOut"></pre>
</div>
</div>

<div id="risk" class="panel">
<div class="card">
<h2>Passive Risk Review</h2>
<textarea id="riskGoal">Act as a passive security and operational risk review team. Use public pages only. Identify exposed workflows, outdated operational patterns, public technical signals, and defensive remediation opportunities. Do not exploit, scan aggressively, login, or attack.</textarea>
<button onclick="riskRun()">Run Passive Review</button>
<pre id="riskOut"></pre>
</div>
</div>

<div id="artifacts" class="panel">
<div class="card">
<h2>Artifacts</h2>
<button onclick="artifactList()">List Artifacts</button>
<pre id="artifactOut"></pre>
</div>
</div>

<script>
function showTab(id){
  document.querySelectorAll(".panel").forEach(p=>p.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}
function print(id,data){
  document.getElementById(id).textContent = typeof data === "string" ? data : JSON.stringify(data,null,2);
}
async function health(){
  const r=await fetch("/health");
  print("dashOut",await r.json());
}
async function capabilities(){
  const r=await fetch("/api/data");
  print("dashOut",await r.json());
}
async function browserRun(){
  const command=document.getElementById("browserCmd").value;
  const r=await fetch("/api/browser",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({command})});
  print("browserOut",await r.json());
}
async function researchRun(){
  const goal=document.getElementById("researchGoal").value;
  const r=await fetch("/api/research",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
    goal,
    niche:"AI automation",
    urls:["https://news.ycombinator.com","https://github.com/trending","https://remoteok.com","https://www.ycombinator.com/companies"],
    max_urls:4,
    make_report:true
  })});
  print("researchOut",await r.json());
}
async function productRun(){
  const goal=document.getElementById("productGoal").value;
  const r=await fetch("/api/product-team",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
    goal,
    niche:"AI automation agency",
    urls:["https://news.ycombinator.com","https://github.com/trending","https://remoteok.com","https://www.ycombinator.com/companies"],
    max_urls:4,
    make_report:true
  })});
  print("productOut",await r.json());
}
async function riskRun(){
  const goal=document.getElementById("riskGoal").value;
  const r=await fetch("/api/research",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
    goal,
    niche:"passive operational risk review",
    urls:["https://owasp.org","https://github.com/trending","https://news.ycombinator.com"],
    max_urls:3,
    make_report:true
  })});
  print("riskOut",await r.json());
}
async function artifactList(){
  const r=await fetch("/api/artifacts");
  print("artifactOut",await r.json());
}
health();
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def root():
    return APP_HTML

@app.get("/app", response_class=HTMLResponse)
def app_ui():
    return APP_HTML

@app.get("/health")
def health():
    return {
        "ok": True,
        "status": "LIVE",
        "uptime": int(time.time() - START_TIME),
        "playwright": PLAYWRIGHT_AVAILABLE,
        "timestamp": now_iso(),
        "version": "10.2-execution",
    }

@app.get("/api/health")
def api_health():
    return health()

@app.get("/api/data")
def api_data():
    return {
        "ok": True,
        "version": "10.2-execution",
        "routes": ["/", "/app", "/health", "/api/browser", "/api/research", "/api/product-team", "/api/artifacts"],
        "capabilities": [
            "browser extraction",
            "multi-source research",
            "product-team opportunity scoring",
            "passive risk review",
            "screenshots",
            "markdown reports",
            "json artifacts",
            "outreach template",
            "pilot pricing",
        ],
        "artifact_dir": ARTIFACT_DIR,
        "screenshot_dir": SCREENSHOT_DIR,
    }

@app.post("/api/exec")
def exec_cmd(cmd: Cmd):
    c = cmd.command.lower().strip()
    if c in ["health", "status"]:
        return health()
    if c in ["help", "capabilities"]:
        return api_data()
    return {"ok": True, "message": "Exec restricted. Use browser/research/product-team.", "received": cmd.command}

@app.post("/api/browser")
async def browser_cmd(cmd: Cmd):
    urls = extract_urls(cmd.command)
    if not urls:
        return {"ok": False, "status": "NEEDS_URL", "example": "extract https://example.com"}
    results = await extract_many(urls[:3], concurrency=2)
    return results[0] if len(results) == 1 else {"ok": True, "count": len(results), "results": results}

@app.post("/api/research")
async def research(task: ResearchTask):
    urls = task.urls or extract_urls(task.goal)
    if not urls:
        urls = ["https://news.ycombinator.com", "https://github.com/trending", "https://remoteok.com", "https://www.ycombinator.com/companies"]
    urls = urls[:task.max_urls]

    results = await extract_many(urls, concurrency=2)
    report, ranked = build_report(task.goal, task.niche or "general", results)

    job_id = f"research_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    report_path = os.path.join(ARTIFACT_DIR, f"{job_id}.md")
    json_path = os.path.join(ARTIFACT_DIR, f"{job_id}.json")

    payload = {
        "ok": True,
        "id": job_id,
        "goal": task.goal,
        "niche": task.niche,
        "urls": urls,
        "results": results,
        "ranked": ranked,
        "report_path": report_path,
        "json_path": json_path,
        "created_at": now_iso(),
    }

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return {
        "ok": True,
        "id": job_id,
        "attempted_urls": urls,
        "successful_extractions": sum(1 for r in results if r.get("ok")),
        "failed_extractions": sum(1 for r in results if not r.get("ok")),
        "report_path": report_path,
        "json_path": json_path,
        "preview": report[:2500],
    }

@app.post("/api/product-team")
async def product_team(task: ResearchTask):
    return await research(task)

@app.get("/api/artifacts")
def artifacts():
    files = []
    for name in sorted(os.listdir(ARTIFACT_DIR), reverse=True):
        path = os.path.join(ARTIFACT_DIR, name)
        if os.path.isfile(path):
            files.append({"name": name, "size": os.path.getsize(path), "path": path})
    return {"ok": True, "count": len(files), "files": files[:50]}

@app.get("/api/artifact/{name}")
def artifact(name: str):
    safe = os.path.basename(name)
    path = os.path.join(ARTIFACT_DIR, safe)
    if not os.path.exists(path):
        return {"ok": False, "error": "artifact not found"}
    return FileResponse(path)
