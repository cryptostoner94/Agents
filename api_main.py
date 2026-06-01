#!/usr/bin/env python3
"""
NEXUS OMEGA - AI Agent Command Center
=====================================
A fully autonomous AI execution platform with:
- FastAPI backend on port 8000
- Playwright browser automation
- Agent loop with task planning and decomposition
- Multi-source research and artifact generation
- Telegram bot bridge
- Shell/code sandbox execution
- LLM integration (when OPENAI_API_KEY is set)

All paths configurable via environment variables.
Defaults to ./data for local deployment.
"""

import os
import json
import re
import time
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.agent_loop import run_agent
from core.browser_operator import extract_page, extract_urls
from core.code_sandbox import run_python
from core.shell_runner import run_shell
from core.memory import log_event, recent

# ======== LLM Configuration ========
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_AVAILABLE = bool(OPENAI_API_KEY)

def call_llm(prompt: str, system: str = None, max_tokens: int = 4000) -> dict:
    """
    Call OpenAI-compatible LLM API.
    Falls back to structured response if no API key.
    """
    if not LLM_AVAILABLE:
        return {
            "ok": False,
            "error": "OPENAI_API_KEY not configured",
            "available": False,
        }
    
    try:
        import urllib.request
        import urllib.error
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": OPENAI_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{OPENAI_BASE_URL}/chat/completions",
            data=data,
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=120) as r:
            response = json.loads(r.read())
            return {
                "ok": True,
                "content": response["choices"][0]["message"]["content"],
                "model": response.get("model", OPENAI_MODEL),
                "usage": response.get("usage", {}),
                "available": True,
            }
    except urllib.error.HTTPError as e:
        return {
            "ok": False,
            "error": f"HTTP {e.code}: {e.reason}",
            "available": True,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "available": True,
        }

# ======== Environment Configuration ========
BASE = Path(os.getenv("NEXUS_BASE", "./data"))
ART = BASE / "artifacts"
SCREENS = BASE / "browser_screens"
STATE = BASE / "state"
STATE.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)
SCREENS.mkdir(parents=True, exist_ok=True)

START = time.time()
PLAYWRIGHT_AVAILABLE = False

try:
    from playwright.async_api import async_playwright as _pw
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    pass

def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# ======== Pydantic Models ========
class ChatTask(BaseModel):
    message: str = ""
    prompt: Optional[str] = None

class BrowserCmd(BaseModel):
    command: str

class BrowserTask(BaseModel):
    url: str
    click_text: Optional[str] = None

class CodeTask(BaseModel):
    code: str

class ShellTask(BaseModel):
    command: str

class ResearchTask(BaseModel):
    goal: str = ""
    urls: List[str] = []
    max_urls: int = 5
    make_report: bool = True

# ======== Helper Functions ========
async def extract_many(urls: List[str], max_urls: int = 5):
    """Extract from multiple URLs concurrently."""
    results = []
    for url in urls[:max_urls]:
        try:
            result = await extract_page(url)
            results.append(result)
        except Exception as e:
            results.append({"ok": False, "url": url, "error": str(e)})
    return results

def generate_artifact(task_id: str, goal: str, results: List[dict]):
    """Generate markdown and JSON artifacts."""
    markdown_path = ART / f"{task_id}.md"
    json_path = ART / f"{task_id}.json"

    lines = [
        f"# NEXUS OMEGA Research Report",
        f"",
        f"**Task ID:** `{task_id}`",
        f"**Goal:** {goal}",
        f"**Generated:** {now()}",
        f"",
        f"## Extraction Results",
        f"",
    ]

    for i, r in enumerate(results, 1):
        if r.get("ok"):
            lines += [
                f"### {i}. {r.get('title', 'Untitled')}",
                f"**URL:** {r.get('final_url', r.get('url', 'N/A'))}",
                f"",
                f"**Preview:**",
                f"```",
                f"{r.get('text_preview', '')[:3000]}",
                f"```",
                f"",
            ]

    markdown = "\n".join(lines)
    payload = {
        "task_id": task_id,
        "goal": goal,
        "generated": now(),
        "results_count": len(results),
        "results": results,
    }

    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return payload

async def run_research(goal: str, urls: List[str], max_urls: int = 5):
    """Run research by extracting from multiple URLs and generating artifacts."""
    if not urls:
        urls = ["https://news.ycombinator.com", "https://github.com/trending"]

    task_id = f"research_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    log_event(task_id, "research_start", {"goal": goal, "urls": urls})

    results = await extract_many(urls, max_urls)

    artifact_payload = None
    if results:
        artifact_payload = generate_artifact(task_id, goal, results)

    log_event(task_id, "research_done", {"results_count": len(results)})

    return {
        "ok": True,
        "task_id": task_id,
        "goal": goal,
        "urls_processed": len(urls),
        "results": results,
        "artifact": artifact_payload,
        "playwright_available": PLAYWRIGHT_AVAILABLE,
        "message": "Research complete. Artifact generated." if artifact_payload else "No results returned."
    }

# ======== HTML Template ========
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
<p class="small">Enter a normal objective, workflow, automation task, URL extraction, or research command.</p>

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

# ======== FastAPI Application ========
app = FastAPI(title="NEXUS OMEGA", version="16.0-complete")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
        "playwright": PLAYWRIGHT_AVAILABLE,
        "llm": {
            "available": LLM_AVAILABLE,
            "model": OPENAI_MODEL if LLM_AVAILABLE else None,
        },
        "timestamp": now(),
        "version": "nexus-omega-fixed",
        "base_path": str(BASE),
        "artifacts_path": str(ART),
        "screens_path": str(SCREENS),
    }

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

    # If LLM is available, use it for intelligent response
    if LLM_AVAILABLE:
        # Extract URLs and context from message
        found_urls = extract_urls(msg)
        context = ""
        
        # If URLs found, extract content first
        if found_urls:
            extracted = await extract_many(found_urls[:3])
            context_parts = []
            for r in extracted:
                if r.get("ok"):
                    context_parts.append(f"URL: {r.get('final_url', r.get('url'))}\nTitle: {r.get('title', '')}\nContent: {r.get('text_preview', '')[:2000]}")
            context = "\n\n".join(context_parts)
        
        # Build prompt for LLM
        system_prompt = """You are NEXUS OMEGA, an advanced AI agent execution system. You help users with:
- Task planning and decomposition
- Browser automation and research
- Code execution and debugging
- Revenue opportunity identification
- Automation workflow design

Always be practical, action-oriented, and provide specific next steps."""

        user_prompt = f"User request: {msg}"
        if context:
            user_prompt += f"\n\nContext from web extraction:\n{context}"
        
        user_prompt += "\n\nProvide a structured response with:\n1. Understanding\n2. Action plan\n3. Specific steps\n4. Expected outcome"
        
        llm_response = call_llm(user_prompt, system=system_prompt)
        
        if llm_response.get("ok"):
            # Save LLM response as artifact
            task_id = f"llm_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            artifact_payload = generate_artifact(task_id, msg, [{"title": "LLM Response", "ok": True, "text_preview": llm_response.get("content", "")}])
            log_event(task_id, "llm_response", {"prompt": msg, "model": llm_response.get("model")})
            
            return {
                "ok": True,
                "mode": "llm-reasoning",
                "llm_model": llm_response.get("model"),
                "llm_usage": llm_response.get("usage", {}),
                "result": llm_response.get("content"),
                "artifact": artifact_payload,
            }
        else:
            # LLM call failed, fall back to research
            return {
                "ok": True,
                "mode": "llm-fallback",
                "llm_error": llm_response.get("error"),
                "result": await run_research(msg, found_urls if found_urls else ["https://news.ycombinator.com", "https://github.com/trending"], 2),
            }

    # No LLM - use browser-based research
    found_urls = extract_urls(msg)

    if found_urls or "extract" in low or "browser" in low:
        url = found_urls[0] if found_urls else "https://example.com"
        result = await extract_page(url)
        return {
            "ok": True,
            "mode": "browser",
            "result": result,
        }

    return {
        "ok": True,
        "mode": "research-only",
        "understanding": "Objective routed to research, scoring, and artifact generation.",
        "result": await run_research(
            goal=msg,
            urls=["https://news.ycombinator.com", "https://github.com/trending"],
            max_urls=2,
        ),
    }

@app.post("/api/browser")
async def browser(cmd: BrowserCmd):
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
            "/", "/app", "/chat",
            "/health",
            "/api/chat", "/api/browser", "/api/research", "/api/product-team",
            "/api/artifacts", "/api/artifact/{name}",
            "/api/exec", "/api/code", "/api/events", "/api/llm",
        ],
        "capabilities": [
            "chat command input", "browser extraction", "research execution",
            "product-team workflow", "artifact generation",
            "markdown report", "json report", "screenshots",
            "code sandbox", "shell execution", "event logging",
            "llm reasoning" if LLM_AVAILABLE else "llm-disabled",
        ],
        "playwright": PLAYWRIGHT_AVAILABLE,
        "llm": {
            "available": LLM_AVAILABLE,
            "model": OPENAI_MODEL if LLM_AVAILABLE else None,
            "base_url": OPENAI_BASE_URL if LLM_AVAILABLE else None,
        },
    }

@app.post("/api/exec")
async def exec_shell(task: ShellTask):
    result = run_shell(task.command)
    return result

@app.post("/api/code")
async def exec_code(task: CodeTask):
    result = run_python(task.code)
    return result

@app.get("/api/events")
def events(limit: int = 30):
    return {"ok": True, "events": recent(limit)}

@app.get("/api/screens")
def screens():
    """List browser screenshots."""
    files = []
    for name in sorted(os.listdir(SCREENS), reverse=True):
        path = f"{SCREENS}/{name}"
        if os.path.isfile(path) and name.endswith('.png'):
            files.append({"name": name, "size": os.path.getsize(path), "path": path})
    return {"ok": True, "count": len(files), "screenshots": files[:20]}

@app.post("/api/llm")
async def llm_chat(req: Request):
    """Direct LLM chat endpoint for advanced reasoning."""
    body = await req.json()
    prompt = body.get("prompt", "")
    system = body.get("system", "")
    max_tokens = body.get("max_tokens", 4000)
    
    if not prompt:
        return {"ok": False, "error": "prompt is required"}
    
    result = call_llm(prompt, system=system, max_tokens=max_tokens)
    return result

@app.get("/api/llm/models")
def llm_models():
    """List available LLM models."""
    return {
        "ok": True,
        "available": LLM_AVAILABLE,
        "current_model": OPENAI_MODEL if LLM_AVAILABLE else None,
        "base_url": OPENAI_BASE_URL,
        "supported": [
            "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo",
            "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
            # Add compatible endpoints for other providers
        ] if LLM_AVAILABLE else [],
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)