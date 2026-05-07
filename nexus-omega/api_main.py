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
app = FastAPI(title="NEXUS OMEGA FINAL STABLE", version="9.5-stable")


class Cmd(BaseModel):
    command: str


class ResearchTask(BaseModel):
    goal: str
    urls: Optional[List[str]] = None
    max_urls: int = 5
    make_report: bool = True


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def clean_text(text: str, limit: int = 12000):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def extract_urls(text: str):
    return re.findall(r"https?://[^\s\"'<>]+", text or "")


async def extract_page(url: str) -> Dict[str, Any]:
    job_id = f"browser_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{job_id}.png")

    if not PLAYWRIGHT_AVAILABLE:
        return {
            "ok": False,
            "url": url,
            "error": "Playwright unavailable",
        }

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

    return await asyncio.gather(*(run_one(url) for url in urls))


def make_report(goal: str, results: List[Dict[str, Any]]):
    lines = []
    lines.append("# NEXUS OMEGA Real-World Research Report")
    lines.append("")
    lines.append(f"Generated: {now_iso()}")
    lines.append("")
    lines.append("## Goal")
    lines.append(goal)
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Sources attempted: {len(results)}")
    lines.append(f"- Successful: {sum(1 for r in results if r.get('ok'))}")
    lines.append(f"- Failed: {sum(1 for r in results if not r.get('ok'))}")
    lines.append("")
    lines.append("## Source Results")

    for i, r in enumerate(results, 1):
        title = r.get("title") or r.get("url") or "Untitled"
        lines.append("")
        lines.append(f"### {i}. {title}")
        lines.append("")
        lines.append(f"- URL: {r.get('url')}")
        lines.append(f"- OK: {r.get('ok')}")
        lines.append(f"- HTTP status: {r.get('status_code')}")
        lines.append(f"- Screenshot: `{r.get('screenshot')}`")

        if r.get("error"):
            lines.append(f"- Error: `{r.get('error')}`")

        lines.append("")
        lines.append("Preview:")
        lines.append("```text")
        lines.append(clean_text(r.get("text_preview", ""), 2500))
        lines.append("```")

    lines.append("")
    lines.append("## Opportunity Rubric")
    lines.append("")
    lines.append("| Factor | Check |")
    lines.append("|---|---|")
    lines.append("| Pain | Is the problem urgent and repeated? |")
    lines.append("| Buyer | Can you directly reach the decision-maker? |")
    lines.append("| Speed | Can a pilot be built in 24-72 hours? |")
    lines.append("| Value | Does it save time, money, or generate revenue? |")
    lines.append("| Automation fit | Can the workflow be automated with browser/API tasks? |")
    lines.append("")
    lines.append("## Practical Offer")
    lines.append("")
    lines.append("Fixed pilot offer: build a small automation/reporting workflow for $300-$750, delivered in 72 hours.")
    lines.append("")
    lines.append("No revenue is guaranteed. This is a lead-intelligence and validation tool.")

    return "\n".join(lines)


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "NEXUS OMEGA",
        "version": "9.5-stable",
        "routes": [
            "/health",
            "/api/health",
            "/api/data",
            "/api/browser",
            "/api/exec",
            "/api/research",
        ],
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
        "capabilities": [
            "health",
            "browser extraction",
            "screenshots",
            "multi-url research",
            "markdown artifact generation",
            "json artifact generation",
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
    return {
        "ok": True,
        "message": "Exec is restricted for safety. Use /api/browser or /api/research.",
        "received": cmd.command,
    }


@app.post("/api/browser")
async def browser_cmd(cmd: Cmd):
    urls = extract_urls(cmd.command)

    if not urls:
        return {
            "ok": False,
            "status": "NEEDS_URL",
            "example": "extract https://example.com",
        }

    results = await extract_many(urls[:3], concurrency=2)

    if len(results) == 1:
        return results[0]

    return {
        "ok": True,
        "count": len(results),
        "results": results,
    }


@app.post("/api/research")
async def research(task: ResearchTask):
    urls = task.urls or extract_urls(task.goal)

    if not urls:
        return {
            "ok": False,
            "error": "No URLs supplied. Provide explicit URLs for reliable research.",
            "example": {
                "goal": "Analyze SMB automation opportunities",
                "urls": ["https://news.ycombinator.com", "https://github.com/cryptostoner94/Agents"],
            },
        }

    urls = urls[: task.max_urls]
    results = await extract_many(urls, concurrency=2)

    job_id = f"research_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    report_text = make_report(task.goal, results)

    report_path = os.path.join(ARTIFACT_DIR, f"{job_id}.md")
    json_path = os.path.join(ARTIFACT_DIR, f"{job_id}.json")

    payload = {
        "ok": True,
        "id": job_id,
        "goal": task.goal,
        "urls": urls,
        "results": results,
        "report_path": report_path,
        "json_path": json_path,
        "created_at": now_iso(),
    }

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

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
        "preview": report_text[:2000],
    }
