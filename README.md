# AGENTS v2 - Elite AI Agent Platform

A fully autonomous AI execution platform with multi-LLM support, browser automation, and real-time task execution.

## Features

- **🌐 Multi-LLM Support**: OpenRouter, OpenAI, Grok, Gemini, HuggingFace, Fireworks
- **🤖 Autonomous Agent**: Task planning, decomposition, and execution
- **🔧 Browser Automation**: Playwright-powered web scraping and interaction
- **💬 Command Center**: Real-time chat interface with live execution
- **📊 Event Logging**: SQLite-backed history of all tasks
- **🚀 Auto-Deploy**: GitHub Actions → AWS EC2 on every push

## Quick Start

```bash
# Clone and setup
git clone https://github.com/cryptostoner94/agents-v2.git
cd agents-v2

# Install dependencies
pip install -r requirements.txt
python -m playwright install chromium

# Run
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Open browser
open http://localhost:8000
```

## Environment Variables

Copy `.env.template` to `.env` and add your API keys:

```bash
cp .env.template .env
```

Key variables:
- `OPENROUTER_API_KEY` - Recommended (access to multiple models)
- `OPENAI_API_KEY` - Direct OpenAI access
- `GROK_API_KEY` - x.ai Grok
- `GEMINI_API_KEY` - Google Gemini
- `PORT` - Server port (default: 8000)

## AWS Deployment

1. Add GitHub Secrets:
   - `EC2_HOST` - Your EC2 public IP
   - `EC2_USER` - Usually `ubuntu`
   - `EC2_SSH_KEY` - Private SSH key

2. Push to `main` branch → Auto-deploys!

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/health` | GET | Health check |
| `/api/chat` | POST | Run agent task |
| `/api/browser` | POST | Browser automation |
| `/api/execute` | POST | Complex task execution |
| `/api/llm/models` | GET | List available models |
| `/api/memory/events` | GET | Event history |

## Architecture

```
agents-v2/
├── app/
│   └── main.py          # FastAPI application
├── core/
│   ├── agent.py         # Agent orchestration
│   ├── llm.py           # Multi-LLM manager
│   ├── browser.py       # Browser automation
│   ├── memory.py        # SQLite event store
│   └── executor.py      # Task execution
├── templates/
│   └── index.html       # Dashboard UI
└── .github/
    └── workflows/
        └── deploy.yml   # Auto-deploy workflow
```

## License

MIT
