#!/usr/bin/env bash
# NEXUS OMEGA - Quick Start Script
# Runs the AI agent platform locally with zero configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "  NEXUS OMEGA - AI Agent Command Center"
echo "========================================="
echo ""

# Create data directories
mkdir -p data/artifacts data/browser_screens data/state/sandbox

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    exit 1
fi

# Check pip
if ! python3 -m pip --version &> /dev/null; then
    echo "ERROR: pip is required but not installed."
    exit 1
fi

# Install dependencies
echo "[1/4] Installing dependencies..."
if [ -f requirements.txt ]; then
    python3 -m pip install --upgrade pip -q
    python3 -m pip install -r requirements.txt -q
fi

# Install playwright browser
echo "[2/4] Installing Playwright Chromium..."
python3 -m playwright install chromium 2>/dev/null || echo "  (Playwright install skipped - may need root)"

# Check syntax
echo "[3/4] Verifying code..."
python3 -m py_compile api_main.py
python3 -m py_compile core/agent_loop.py
python3 -m py_compile core/browser_operator.py
python3 -m py_compile core/code_sandbox.py
python3 -m py_compile core/shell_runner.py
python3 -m py_compile core/memory.py
python3 -m py_compile core/policy.py
echo "  All modules OK"

# Start the server
echo "[4/4] Starting NEXUS OMEGA..."
PORT="${PORT:-8000}"
echo ""
echo "========================================="
echo "  NEXUS OMEGA is starting..."
echo "  Open: http://localhost:$PORT/chat"
echo "  Health: http://localhost:$PORT/health"
echo "========================================="
echo ""

python3 -m uvicorn api_main:app --host 0.0.0.0 --port "$PORT" --reload
