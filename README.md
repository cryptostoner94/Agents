# NEXUS OMEGA - AI Agent Command Center

A fully autonomous AI execution platform with browser automation, research capabilities, and real-time task execution.

## Features

- **AI Command Center Dashboard** - Web UI with chat interface
- **Browser Automation** - Playwright-powered web scraping and interaction
- **Agent Loop** - Task planning, decomposition, and execution
- **Multi-Source Research** - Extract from multiple URLs concurrently
- **Artifact Generation** - Markdown and JSON reports
- **Code Sandbox** - Safe Python code execution
- **Shell Execution** - Safe shell commands with allowlist
- **Telegram Bot** - Control via Telegram (optional)
- **Event Logging** - SQLite-backed event history

## Quick Start

### One-Command Run

```bash
bash install.sh
```

Or manually:

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
python -m playwright install chromium

# Run the server
python3 -m uvicorn api_main:app --host 0.0.0.0 --port 8000
```

Then open: **http://localhost:8000/chat**

### Smoke Test

```bash
# In another terminal, run tests
python3 smoke_test.py
```

## Architecture

```
api_main.py          # Main FastAPI application (port 8000)
├── core/
│   ├── agent_loop.py       # Agent orchestration logic
│   ├── browser_operator.py # Playwright web extraction
│   ├── code_sandbox.py     # Safe Python execution
│   ├── shell_runner.py     # Shell command execution
│   ├── memory.py           # SQLite event logging
│   └── policy.py           # Safety checks
├── tg_bot.py          # Telegram bot (optional)
├── smoke_test.py      # Smoke test suite
├── requirements.txt   # Python dependencies
├── install.sh         # Quick start script
└── run.sh             # Configurable run script
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Chat UI |
| `/chat` | GET | Chat UI |
| `/health` | GET | Health status |
| `/api/chat` | POST | Run agent task |
| `/api/browser` | POST | Browser extraction |
| `/api/research` | POST | Run research |
| `/api/product-team` | POST | Run product team workflow |
| `/api/artifacts` | GET | List artifacts |
| `/api/artifact/{name}` | GET | Download artifact |
| `/api/data` | GET | System capabilities |
| `/api/exec` | POST | Run shell command |
| `/api/code` | POST | Run Python code |
| `/api/events` | GET | Event history |
| `/api/screens` | GET | Browser screenshots |

## Environment Variables

Copy `.env.template` to `.env` and configure:

```bash
NEXUS_BASE=./data          # Base directory (default: ./data)
PORT=8000                  # Server port (default: 8000)
OPENAI_API_KEY=...         # Optional: LLM provider
TG_TOKEN=...               # Optional: Telegram bot
```

## Deployment Options

### Local Development
```bash
bash install.sh
```

### Docker (Coming Soon)
```bash
docker build -t nexus-omega .
docker run -p 8000:8000 -v ./data:/app/data nexus-omega
```

### Cloud (Railway/Render/Fly.io)
1. Set `NEXUS_BASE` to a persistent volume path
2. Set `PORT` if needed (default 8000)
3. Deploy with your chosen platform

## Status

- ✅ All routes functional
- ✅ Browser automation with Playwright
- ✅ Code sandbox execution
- ✅ Artifact generation
- ✅ SQLite event logging
- ✅ Telegram bot ready (optional)
- ✅ Smoke tests passing
- ✅ Portable paths (no hardcoded `/opt/`)

## Notes

- Browser extraction requires `playwright` and `chromium`
- Shell commands are restricted to safe allowlist
- Code sandbox blocks dangerous imports
- Without API keys, runs in local-only mode
