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
