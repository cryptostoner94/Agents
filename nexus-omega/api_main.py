import os, re, json, time, uuid, asyncio, traceback
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

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
app = FastAPI(title="NEXUS OMEGA Product Team Agent", version="10.0-stable")

class Cmd(BaseModel):
    command: str

class ResearchTask(BaseModel):
    goal: str
    urls: Optional[List[str]] = None
    niche: Optional[str] = "small business automation"
    max_urls: int = 6
    make_report: bool = True

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def clean_text(text: str, limit: int = 12000):
    return re.sub(r"\s+", " ", text or "").strip()[:limit]

def extract_urls(text: str):
    return re.findall(r"https?://[^\s\"'<>]+", text or "")

def default_sources(niche: str):
    return [
        "https://news.ycombinator.com",
        "https://www.ycombinator.com/companies",
        "https://www.producthunt.com",
        "https://www.reddit.com/r/smallbusiness/",
        "https://www.reddit.com/r/Entrepreneur/",
        "https://github.com/cryptostoner94/Agents",
    ]

async def extract_page(url: str) -> Dict[str, Any]:
    job_id = f"browser_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{job_id}.png")

    if not PLAYWRIGHT_AVAILABLE:
        return {"ok": False, "url": url, "error": "Playwright unavailable"}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )
            page = await browser.new_page(
                viewport={"width": 1365, "height": 900},
                user_agent="Mozilla/5.0 Chrome/122 Safari/537.36"
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
    return await asyncio.gather(*(run_one(url) for url in urls))

def score_opportunity(text: str):
    t = text.lower()
    score = 0
    signals = []

    checks = {
        "hiring": ["hiring", "jobs", "careers", "engineer", "operations", "support"],
        "manual_work": ["manual", "spreadsheet", "email", "admin", "workflow", "support"],
        "automation_fit": ["automation", "agent", "api", "browser", "report", "scrape"],
        "buyer_pain": ["delay", "slow", "cost", "scale", "customer", "repetitive"],
        "fast_pilot": ["small business", "startup", "clinic", "agency", "local", "smb"],
    }

    for label, words in checks.items():
        if any(w in t for w in words):
            score += 2
            signals.append(label)

    return min(score, 10), signals

def product_team_report(goal: str, niche: str, results: List[Dict[str, Any]]):
    rows = []
    for r in results:
        text = r.get("text_preview", "")
        score, signals = score_opportunity(text)
        rows.append({
            "source": r.get("title") or r.get("url"),
            "url": r.get("url"),
            "ok": r.get("ok"),
            "score": score,
            "signals": signals,
            "pilot_offer": "72-hour automation audit + prototype",
            "price_range": "$300-$750 pilot",
            "next_action": "Extract buyer/contact path and send targeted pilot offer",
            "screenshot": r.get("screenshot"),
            "preview": clean_text(text, 1200),
        })

    rows = sorted(rows, key=lambda x: x["score"], reverse=True)

    md = []
    md.append("# NEXUS OMEGA Product Team Execution Report")
    md.append("")
    md.append(f"Generated: {now_iso()}")
    md.append("")
    md.append("## Mission")
    md.append(goal)
    md.append("")
    md.append("## Niche")
    md.append(niche)
    md.append("")
    md.append("## Executive Verdict")
    md.append("This run produced a real browser-extracted opportunity scan and created deliverables for lead intelligence, pilot pricing, and next actions.")
    md.append("")
    md.append("## Ranked Opportunities")
    md.append("")
    md.append("| Rank | Source | Score | Signals | Pilot Offer | Price |")
    md.append("|---:|---|---:|---|---|---|")
    for i, row in enumerate(rows, 1):
        md.append(f"| {i} | {row['source']} | {row['score']} | {', '.join(row['signals'])} | {row['pilot_offer']} | {row['price_range']} |")

    md.append("")
    md.append("## Top 3 Actions")
    for i, row in enumerate(rows[:3], 1):
        md.append("")
        md.append(f"### {i}. {row['source']}")
        md.append(f"- URL: {row['url']}")
        md.append(f"- Score: {row['score']}/10")
        md.append(f"- Signals: {', '.join(row['signals'])}")
        md.append(f"- Screenshot: `{row['screenshot']}`")
        md.append("- Offer: build a small browser/API automation that saves 3-5 hours weekly.")
        md.append("- Price: $300-$750 fixed pilot.")
        md.append("- Contact angle: operational inefficiency, manual work, reporting, support, admin load.")
        md.append("")
        md.append("Preview:")
        md.append("```text")
        md.append(row["preview"])
        md.append("```")

    md.append("")
    md.append("## Cold Outreach Template")
    md.append("")
    md.append("Subject: Quick automation pilot for your operations workflow")
    md.append("")
    md.append("Hi {{name}},")
    md.append("")
    md.append("I noticed signs that your team may be dealing with repetitive admin, reporting, support, or workflow tasks.")
    md.append("")
    md.append("I build small automation pilots that use browser/API workflows to reduce manual work. I can deliver a working prototype within 72 hours for a fixed pilot fee.")
    md.append("")
    md.append("Would you be open to a short walkthrough this week?")
    md.append("")
    md.append("Best,")
    md.append("{{your_name}}")
    md.append("")
    md.append("## Caveat")
    md.append("This system creates lead intelligence and execution artifacts. It does not guarantee revenue. Manual verification and outreach are still required.")

    return "\n".join(md), rows

@app.get("/")
def root():
    return {
        "ok": True,
        "service": "NEXUS OMEGA",
        "version": "10.0-stable",
        "routes": ["/health", "/api/health", "/api/data", "/api/browser", "/api/research", "/api/product-team", "/api/exec"],
    }

@app.get("/health")
def health():
    return {
        "ok": True,
        "status": "LIVE",
        "uptime": int(time.time() - START_TIME),
        "playwright": PLAYWRIGHT_AVAILABLE,
        "timestamp": now_iso(),
    }

@app.get("/api/health")
def api_health():
    return health()

@app.get("/api/data")
def api_data():
    return {
        "ok": True,
        "version": "10.0-stable",
        "capabilities": [
            "browser extraction",
            "screenshots",
            "multi-url research",
            "product-team opportunity scoring",
            "markdown reports",
            "json datasets",
            "cold outreach template",
            "pilot pricing recommendation",
        ],
        "artifact_dir": ARTIFACT_DIR,
        "screenshot_dir": SCREENSHOT_DIR,
    }

@app.post("/api/exec")
def exec_cmd(cmd: Cmd):
    c = cmd.command.lower().strip()
    if c in ["status", "health"]:
        return health()
    if c in ["help", "capabilities"]:
        return api_data()
    return {"ok": True, "message": "Exec restricted. Use /api/browser, /api/research, or /api/product-team.", "received": cmd.command}

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
        urls = default_sources(task.niche or "small business automation")
    urls = urls[:task.max_urls]
    results = await extract_many(urls, concurrency=2)

    job_id = f"research_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    report, rows = product_team_report(task.goal, task.niche or "general", results)

    report_path = os.path.join(ARTIFACT_DIR, f"{job_id}.md")
    json_path = os.path.join(ARTIFACT_DIR, f"{job_id}.json")

    payload = {"ok": True, "id": job_id, "goal": task.goal, "urls": urls, "results": results, "ranked": rows, "report_path": report_path, "json_path": json_path, "created_at": now_iso()}

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return {"ok": True, "id": job_id, "attempted_urls": urls, "successful_extractions": sum(1 for r in results if r.get("ok")), "failed_extractions": sum(1 for r in results if not r.get("ok")), "report_path": report_path, "json_path": json_path, "preview": report[:2200]}

@app.post("/api/product-team")
async def product_team(task: ResearchTask):
    return await research(task)
