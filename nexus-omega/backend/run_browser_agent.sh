#!/usr/bin/env bash
cd /home/cryptostoner94/nexus-omega
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi
exec python3 agents/browser_agent.py "$@"
