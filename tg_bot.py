#!/usr/bin/env python3
"""
NEXUS OMEGA - Telegram Bot
Receives commands via Telegram and forwards to the backend API.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path

# Load environment
APP_DIR = Path(os.getenv("NEXUS_BASE", "./data")).parent
SECRETS = APP_DIR / ".env"

def load_env():
    """Load environment variables from .env file."""
    env = {}
    if SECRETS.exists():
        for line in SECRETS.read_text().splitlines():
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    # Also check os.environ
    for k, v in os.environ.items():
        if k not in env:
            env[k] = v
    return env

ENV = load_env()
TG_TOKEN = ENV.get("TG_TOKEN") or os.getenv("TG_TOKEN", "")
API_HOST = ENV.get("API_HOST", "http://127.0.0.1:8000")

def api_call(method, payload=None):
    """Call the Telegram Bot API."""
    data = urllib.parse.urlencode(payload or {}).encode()
    url = f"https://api.telegram.org/bot{TG_TOKEN}/{method}"
    with urllib.request.urlopen(url, data=data, timeout=60) as r:
        return json.loads(r.read())

def send_message(chat_id, text):
    """Send a message to a Telegram chat."""
    try:
        api_call("sendMessage", {"chat_id": chat_id, "text": text[:3900]})
    except Exception as e:
        print(f"Failed to send message: {e}", flush=True)

def forward_to_backend(endpoint, data):
    """Forward a request to the backend API."""
    url = f"{API_HOST}{endpoint}"
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}

def handle_command(chat_id, text):
    """Handle a command from Telegram."""
    text = text.strip()
    low = text.lower()

    # Help command
    if text in ["/start", "/help", "/commands"]:
        return (
            "NEXUS OMEGA Commands:\n\n"
            "Status:\n"
            "/status - System status\n"
            "/health - Health check\n\n"
            "Agent:\n"
            "/agent <task> - Run agent task\n"
            "/chat <message> - Chat with agent\n\n"
            "Browser:\n"
            "/browser <url> - Extract URL\n"
            "/browser_status - Browser status\n\n"
            "Research:\n"
            "/research <goal> - Run research"
        )

    # Health check
    if text == "/health":
        result = forward_to_backend("/health", {})
        return json.dumps(result, indent=2)[:3900]

    # Status check
    if text == "/status":
        result = forward_to_backend("/api/data", {})
        return json.dumps(result, indent=2)[:3900]

    # Agent task
    if text.startswith("/agent "):
        task = text[7:].strip()
        result = forward_to_backend("/api/chat", {"message": task})
        return json.dumps(result, indent=2)[:3900]

    # Chat
    if text.startswith("/chat "):
        msg = text[6:].strip()
        result = forward_to_backend("/api/chat", {"message": msg})
        return json.dumps(result, indent=2)[:3900]

    # Browser extraction
    if text.startswith("/browser "):
        url = text[9:].strip()
        result = forward_to_backend("/api/browser", {"command": f"extract {url}"})
        return json.dumps(result, indent=2)[:3900]

    # Research
    if text.startswith("/research "):
        goal = text[10:].strip()
        result = forward_to_backend("/api/research", {"goal": goal})
        return json.dumps(result, indent=2)[:3900]

    # Unknown command
    return "Unknown command. Use /help for available commands."

def main():
    if not TG_TOKEN:
        print("ERROR: TG_TOKEN not set. Set it in .env file or as environment variable.", flush=True)
        print(f"Checked .env at: {SECRETS}", flush=True)
        sys.exit(1)

    print(f"NEXUS OMEGA Telegram Bot starting...", flush=True)
    print(f"API Host: {API_HOST}", flush=True)

    # Delete webhook to enable polling
    try:
        api_call("deleteWebhook", {"drop_pending_updates": "true"})
    except Exception:
        pass

    offset = 0
    while True:
        try:
            updates = api_call("getUpdates", {"timeout": 50, "offset": offset})
            for u in updates.get("result", []):
                offset = max(offset, u["update_id"] + 1)
                msg = u.get("message") or u.get("edited_message")
                if msg:
                    chat_id = (msg.get("chat") or {}).get("id")
                    text = msg.get("text", "")
                    if chat_id and text:
                        reply = handle_command(chat_id, text)
                        send_message(chat_id, reply)
        except Exception as e:
            print(f"Poll error: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    main()