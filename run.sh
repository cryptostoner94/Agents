#!/usr/bin/env bash
# NEXUS OMEGA - Run with Options
# Usage: bash run.sh [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
PORT="${PORT:-8000}"
RELOAD=""
HOST="0.0.0.0"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port=*)
            PORT="${1#*=}"
            ;;
        --host=*)
            HOST="${1#*=}"
            ;;
        --reload)
            RELLOAD="--reload"
            ;;
        --no-reload)
            RELOAD=""
            ;;
        --help)
            echo "NEXUS OMEGA - Run Script"
            echo ""
            echo "Usage: bash run.sh [options]"
            echo ""
            echo "Options:"
            echo "  --port=PORT     Set server port (default: 8000)"
            echo "  --host=HOST     Set server host (default: 0.0.0.0)"
            echo "  --reload        Enable auto-reload"
            echo "  --no-reload     Disable auto-reload"
            echo "  --help          Show this help"
            echo ""
            echo "Environment variables:"
            echo "  PORT            Server port"
            echo "  NEXUS_BASE      Base directory for data"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage"
            exit 1
            ;;
    esac
    shift
done

# Create data directories
mkdir -p data/artifacts data/browser_screens data/state/sandbox

echo ""
echo "========================================="
echo "  NEXUS OMEGA"
echo "  Port: $PORT"
echo "  Host: $HOST"
echo "========================================="
echo ""
echo "  Dashboard: http://localhost:$PORT/chat"
echo "  Health:    http://localhost:$PORT/health"
echo "  API:       http://localhost:$PORT/api/data"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

python3 -m uvicorn api_main:app --host "$HOST" --port "$PORT" $RELOAD