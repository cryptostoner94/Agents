"""
AGENTS v2 - Elite AI Agent Platform
Multi-LLM powered autonomous agent with browser automation
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import WebSocket

# Import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.agent import AgentCore
from core.llm import LLManager
from core.browser import BrowserOperator
from core.memory import MemoryStore
from core.executor import TaskExecutor

# ============== APP SETUP ==============
app = FastAPI(
    title="AGENTS - Elite AI Agent Platform",
    version="2.0.0",
    description="Multi-LLM powered autonomous agent with browser automation"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== CORE INSTANCES ==============
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = os.getenv("AGENTS_DATA_DIR", str(BASE_DIR / "data"))
os.makedirs(DATA_DIR, exist_ok=True)

llm_manager = LLManager()
agent = AgentCore(llm_manager)
browser = BrowserOperator()
memory = MemoryStore(DATA_DIR)
executor = TaskExecutor(agent, browser, memory)

# ============== ROUTES ==============

@app.get("/", response_class=HTMLResponse)
@app.get("/chat", response_class=HTMLResponse)
async def home():
    """Main dashboard UI"""
    html_path = BASE_DIR / "templates" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse(content=generate_dashboard_html())

@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse({
        "status": "ok",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "llm_providers": llm_manager.get_providers(),
        "capabilities": {
            "browser": browser.is_available(),
            "agent": True,
            "executor": True
        }
    })

@app.post("/api/chat")
async def chat(request: dict):
    """Main chat endpoint - runs agent task"""
    try:
        task = request.get("task", "")
        model = request.get("model", "auto")
        
        if not task:
            return JSONResponse({"error": "No task provided"}, status_code=400)
        
        result = await agent.run_task(task, model=model)
        await memory.log_event("task", {"task": task, "result": result})
        
        return JSONResponse({
            "success": True,
            "task": task,
            "result": result,
            "model": model
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/browser")
async def browser_task(request: dict):
    """Browser automation endpoint"""
    try:
        action = request.get("action", "extract")
        url = request.get("url", "")
        instructions = request.get("instructions", "")
        
        if action == "extract" and url:
            result = await browser.extract(url, instructions)
        elif action == "interact":
            result = await browser.interact(url, instructions)
        else:
            result = {"error": "Invalid action"}
        
        return JSONResponse({"success": True, "result": result})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/execute")
async def execute_task(request: dict):
    """Execute complex task with planning"""
    try:
        task = request.get("task", "")
        result = await executor.execute(task)
        return JSONResponse({"success": True, "result": result})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/llm/models")
async def list_models():
    """List available LLM models"""
    return JSONResponse({
        "providers": llm_manager.get_providers(),
        "models": llm_manager.list_models()
    })

@app.get("/api/memory/events")
async def get_events(limit: int = 50):
    """Get event history"""
    events = memory.get_events(limit)
    return JSONResponse({"events": events})

@app.get("/api/status")
async def status():
    """Full system status"""
    return JSONResponse({
        "system": "operational",
        "llm_connected": llm_manager.is_connected(),
        "browser_connected": browser.is_available(),
        "memory_size": memory.size(),
        "data_dir": DATA_DIR
    })

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process incoming message
            message = json.loads(data)
            if message.get("type") == "task":
                result = await agent.run_task(message.get("task", ""))
                await websocket.send_json({"type": "result", "data": result})
    except Exception as e:
        await websocket.send_json({"type": "error", "error": str(e)})

# ============== MAIN ==============
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
