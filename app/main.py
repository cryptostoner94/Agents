"""AGENTS v2 - Standalone Elite AI Agent Platform"""
import os
import sys
import json
import sqlite3
import aiohttp
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(title="AGENTS v2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

DATA_DIR = "./data"
Path(DATA_DIR).mkdir(exist_ok=True)

# ===== DASHBOARD HTML =====
DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AGENTS v2 - Elite AI Agent Platform</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0a0a0f;color:#fff;min-height:100vh}
header{background:linear-gradient(135deg,#1a1a2e,#16213e);border-bottom:1px solid #2d2d44;padding:20px}
header h1{font-size:28px;background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.container{max-width:1100px;margin:0 auto;padding:20px}
.status{display:inline-block;padding:6px 14px;border-radius:15px;background:rgba(72,199,116,0.2);border:1px solid #48c774;color:#48c774;margin-left:20px;font-size:13px}
.chat{background:#13131f;border-radius:16px;border:1px solid #2d2d44;overflow:hidden}
.chat-header{padding:18px;background:linear-gradient(135deg,#1a1a2e,#16213e);border-bottom:1px solid #2d2d44}
.chat-header h2{font-size:18px;margin-bottom:4px}
.chat-header p{color:#888;font-size:12px}
.msgs{height:380px;overflow-y:auto;padding:20px}
.msg{margin-bottom:14px;padding:12px 16px;border-radius:12px;max-width:85%}
.msg.user{background:linear-gradient(135deg,#667eea,#764ba2);margin-left:auto}
.msg.agent{background:#1e1e2e;border:1px solid #2d2d44}
.input-area{padding:16px;border-top:1px solid #2d2d44;display:flex;gap:10px}
.input{flex:1;padding:12px 16px;border-radius:10px;border:1px solid #2d2d44;background:#0a0a0f;color:#fff;font-size:14px;outline:none}
.input:focus{border-color:#667eea}
.btn{padding:12px 24px;border-radius:10px;border:none;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font-size:14px;font-weight:600;cursor:pointer}
.btn:hover{transform:scale(1.03)}
.loading{padding:12px 20px;color:#888;font-size:13px;display:none}
.loading.active{display:flex;align-items:center;gap:8px}
.spinner{width:16px;height:16px;border:2px solid #2d2d44;border-top-color:#667eea;border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.providers{margin-top:20px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.provider{background:#13131f;border:1px solid #2d2d44;border-radius:10px;padding:16px;text-align:center}
.provider .dot{width:10px;height:10px;border-radius:50%;background:#f1838d;display:block;margin:0 auto 8px}
.provider.on{border-color:#48c774}
.provider.on .dot{background:#48c774}
</style>
</head>
<body>
<header><div class="container" style="display:flex;align-items:center">
<h1>⚡ AGENTS v2</h1><span class="status" id="status">● Online</span>
</div></header>
<div class="container">
<div class="chat">
<div class="chat-header"><h2>🎯 Command Center</h2><p>Elite AI Agent - ask anything, automate tasks</p></div>
<div class="msgs" id="msgs"><div class="msg agent"><strong>AGENTS v2.0</strong> ready!<br><br>🎯 I can help with:<br>• Research & data extraction<br>• Task automation<br>• Browser operations<br>• Coding & debugging<br><br>What would you like me to do?</div></div>
<div class="loading" id="loading"><div class="spinner"></div><span>Processing...</span></div>
<div class="input-area">
<input class="input" id="input" placeholder="Enter your task..." onkeypress="if(event.key==='Enter')send()">
<button class="btn" onclick="send()">Send</button>
</div></div>
<div class="providers" id="providers">
<div class="provider" id="p-openrouter"><div class="dot"></div>OpenRouter</div>
<div class="provider" id="p-grok"><div class="dot"></div>Grok</div>
<div class="provider" id="p-gemini"><div class="dot"></div>Gemini</div>
<div class="provider" id="p-openai"><div class="dot"></div>OpenAI</div>
</div></div>
<script>
async function send(){
  const inp=document.getElementById('input');
  const msg=inp.value.trim();
  if(!msg)return;
  addMsg(msg,'user');
  inp.value='';
  document.getElementById('loading').classList.add('active');
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:msg})});
    const d=await r.json();
    document.getElementById('loading').classList.remove('active');
    addMsg(d.result?.response||d.result||d.error||'Error','agent');
  }catch(e){document.getElementById('loading').classList.remove('active');addMsg('Connection error - server not responding','agent');}
}
function addMsg(text,type){
  const div=document.createElement('div');
  div.className='msg '+type;
  div.innerHTML=text+'<div style="font-size:11px;color:#555;margin-top:6px">'+new Date().toLocaleTimeString()+'</div>';
  document.getElementById('msgs').appendChild(div);
  document.getElementById('msgs').scrollTop=document.getElementById('msgs').scrollHeight;
}
fetch('/health').then(r=>r.json()).then(d=>{
  (d.providers||[]).forEach(p=>{const el=document.getElementById('p-'+p);if(el)el.classList.add('on');});
}).catch(()=>{});
</script>
</body>
</html>"""

# ===== LLM PROVIDER =====
class LLMProvider:
    def __init__(self):
        self.providers = {}
        self._load_providers()
    
    def _load_providers(self):
        # OpenRouter
        key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if key:
            self.providers["openrouter"] = {
                "name": "OpenRouter",
                "key": key,
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "models": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "google/gemini-2.0-flash"]
            }
        # Grok
        key = os.getenv("GROK_API_KEY")
        if key:
            self.providers["grok"] = {"name": "Grok", "key": key, "url": "https://api.x.ai/v1/chat/completions", "models": ["grok-2-1212"]}
        # Gemini
        key = os.getenv("GEMINI_API_KEY")
        if key:
            self.providers["gemini"] = {"name": "Gemini", "key": key, "url": "https://generativelanguage.googleapis.com/v1beta/models", "models": ["gemini-2.0-flash-exp"]}
    
    def get_names(self):
        return list(self.providers.keys())
    
    def is_configured(self):
        return len(self.providers) > 0
    
    async def generate(self, prompt):
        if not self.providers:
            return self._demo_response(prompt)
        
        # Use first provider
        p = list(self.providers.values())[0]
        try:
            async with aiohttp.ClientSession() as s:
                headers = {"Authorization": f"Bearer {p['key']}", "Content-Type": "application/json"}
                model = p['models'][0]
                
                if p['name'] == 'Gemini':
                    url = f"{p['url']}/{model}:generateContent?key={p['key']}"
                    data = {"contents": [{"parts": [{"text": prompt}]}]}
                else:
                    url = p['url']
                    data = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2048}
                
                async with s.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(60)) as r:
                    if r.status == 200:
                        result = await r.json()
                        if p['name'] == 'Gemini':
                            return result['candidates'][0]['content']['parts'][0]['text']
                        return result['choices'][0]['message']['content']
                    else:
                        return f"API Error ({r.status}): {await r.text()}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _demo_response(self, prompt):
        return f"""AGENTS v2 is operational!

Task received: "{prompt[:80]}..."

I'm ready to help but need an API key configured. Add one of these to your .env file:
• OPENROUTER_API_KEY (recommended - multiple models)
• GROK_API_KEY  
• GEMINI_API_KEY
• OPENAI_API_KEY

Once configured, I'll provide full AI-powered responses."""

# ===== MEMORY =====
def init_db():
    db_path = Path(DATA_DIR) / "memory.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, type TEXT, data TEXT, ts TEXT)")
    conn.commit()
    conn.close()

def log_event(event_type, data):
    db_path = Path(DATA_DIR) / "memory.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("INSERT INTO events (type, data, ts) VALUES (?, ?, ?)", (event_type, json.dumps(data), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

init_db()
llm = LLMProvider()

# ===== ROUTES =====
@app.get("/", response_class=HTMLResponse)
@app.get("/chat", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=DASHBOARD)

@app.get("/health")
async def health():
    return JSONResponse({
        "status": "ok",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "providers": llm.get_names(),
        "configured": llm.is_configured()
    })

@app.post("/api/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        task = body.get("task", "")
        
        if not task:
            return JSONResponse({"error": "No task provided"}, status_code=400)
        
        # Log event
        log_event("task", {"task": task, "timestamp": datetime.utcnow().isoformat()})
        
        # Generate response
        response = await llm.generate(task)
        
        return JSONResponse({
            "success": True,
            "result": {"response": response, "task": task},
            "providers": llm.get_names()
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/status")
async def status():
    return JSONResponse({
        "system": "operational",
        "llm_configured": llm.is_configured(),
        "providers": llm.get_names(),
        "uptime": "running"
    })

# ===== RUN =====
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀 AGENTS v2 starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
