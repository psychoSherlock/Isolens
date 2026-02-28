#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
#  IsoLens — Full Project Launcher
# ═══════════════════════════════════════════════════════════
#  Starts all services:
#    1. FastAPI Gateway   (port 6969)
#    2. Next.js Interface (port 3000)
#
#  Usage:
#    ./run.sh          Start everything
#    ./run.sh stop     Stop all IsoLens processes
#
#  Ctrl+C stops all services gracefully.
# ═══════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
INTERFACE_DIR="${PROJECT_ROOT}/core/interface"

GATEWAY_PORT=6969
INTERFACE_PORT=3000
AGENT_IP="192.168.56.105"
AGENT_PORT=9090

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No colour

PIDS=()

# ─── Helpers ──────────────────────────────────────────────

log()  { echo -e "${CYAN}[IsoLens]${NC} $*"; }
ok()   { echo -e "${GREEN}  ✔${NC} $*"; }
warn() { echo -e "${YELLOW}  ⚠${NC} $*"; }
err()  { echo -e "${RED}  ✘${NC} $*"; }

banner() {
    echo ""
    echo -e "${BOLD}${CYAN}"
    echo "  ╔══════════════════════════════════════════╗"
    echo "  ║         IsoLens Sandbox Platform         ║"
    echo "  ╚══════════════════════════════════════════╝"
    echo -e "${NC}"
}

cleanup() {
    echo ""
    log "Shutting down services..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            wait "$pid" 2>/dev/null || true
        fi
    done
    # Make sure nothing lingers
    pkill -f "uvicorn core.gateway.app" 2>/dev/null || true
    pkill -f "next dev.*--port ${INTERFACE_PORT}" 2>/dev/null || true
    ok "All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# ─── Stop mode ────────────────────────────────────────────

if [[ "${1:-}" == "stop" ]]; then
    log "Stopping all IsoLens services..."
    pkill -f "uvicorn core.gateway.app" 2>/dev/null && ok "Gateway stopped" || warn "Gateway was not running"
    pkill -f "next dev" 2>/dev/null && ok "Interface stopped" || warn "Interface was not running"
    exit 0
fi

# ─── Pre-flight checks ───────────────────────────────────

banner

log "Running pre-flight checks..."

# Python venv
if [[ ! -f "${VENV_PYTHON}" ]]; then
    err "Python venv not found at ${VENV_PYTHON}"
    log "Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi
ok "Python venv found"

# Python dependencies
if ! "${VENV_PYTHON}" -c "import fastapi, uvicorn, httpx" 2>/dev/null; then
    warn "Missing Python packages — installing..."
    "${VENV_PYTHON}" -m pip install -q -r "${PROJECT_ROOT}/requirements.txt"
    ok "Python dependencies installed"
else
    ok "Python dependencies OK"
fi

# Node.js
if ! command -v node &>/dev/null; then
    err "Node.js not found — install Node.js 18+ first"
    exit 1
fi
ok "Node.js $(node --version)"

# npm dependencies
if [[ ! -d "${INTERFACE_DIR}/node_modules" ]]; then
    warn "node_modules missing — installing..."
    (cd "${INTERFACE_DIR}" && npm install --silent)
    ok "npm dependencies installed"
else
    ok "npm dependencies OK"
fi

# Check for port conflicts
if lsof -i ":${GATEWAY_PORT}" -sTCP:LISTEN &>/dev/null; then
    warn "Port ${GATEWAY_PORT} already in use — killing existing process"
    pkill -f "uvicorn core.gateway.app" 2>/dev/null || true
    sleep 1
fi

if lsof -i ":${INTERFACE_PORT}" -sTCP:LISTEN &>/dev/null; then
    warn "Port ${INTERFACE_PORT} already in use — killing existing process"
    pkill -f "next dev" 2>/dev/null || true
    sleep 1
fi

echo ""

# ─── Start Gateway ────────────────────────────────────────

log "Starting Gateway on port ${GATEWAY_PORT}..."
cd "${PROJECT_ROOT}"
"${VENV_PYTHON}" -m uvicorn core.gateway.app:app \
    --host 0.0.0.0 \
    --port "${GATEWAY_PORT}" \
    --log-level info \
    &>"${PROJECT_ROOT}/gateway.log" &
PIDS+=($!)
GATEWAY_PID=${PIDS[-1]}

# Wait for gateway to be ready
for i in {1..15}; do
    if curl -s --max-time 1 "http://127.0.0.1:${GATEWAY_PORT}/api/ping" | grep -q "pong" 2>/dev/null; then
        ok "Gateway ready  →  http://localhost:${GATEWAY_PORT}  (PID ${GATEWAY_PID})"
        break
    fi
    if [[ $i -eq 15 ]]; then
        err "Gateway failed to start — check gateway.log"
        cat "${PROJECT_ROOT}/gateway.log" | tail -20
        cleanup
    fi
    sleep 1
done

# ─── Start Interface ─────────────────────────────────────

log "Starting Interface on port ${INTERFACE_PORT}..."
cd "${INTERFACE_DIR}"
npx next dev --port "${INTERFACE_PORT}" \
    &>"${PROJECT_ROOT}/interface.log" &
PIDS+=($!)
INTERFACE_PID=${PIDS[-1]}

# Wait for interface to be ready
for i in {1..30}; do
    if curl -s --max-time 2 -o /dev/null -w "%{http_code}" "http://localhost:${INTERFACE_PORT}" 2>/dev/null | grep -qE "200|307"; then
        ok "Interface ready →  http://localhost:${INTERFACE_PORT}  (PID ${INTERFACE_PID})"
        break
    fi
    if [[ $i -eq 30 ]]; then
        warn "Interface is compiling — it may take a moment on first load"
    fi
    sleep 1
done

# ─── Check VM Agent (optional) ───────────────────────────

echo ""
log "Checking sandbox VM agent..."
if curl -s --max-time 3 "http://${AGENT_IP}:${AGENT_PORT}/api/status" | grep -q '"status"' 2>/dev/null; then
    AGENT_VER=$(curl -s --max-time 3 "http://${AGENT_IP}:${AGENT_PORT}/api/status" 2>/dev/null \
        | "${VENV_PYTHON}" -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('agent_version','?'))" 2>/dev/null || echo "?")
    ok "VM Agent v${AGENT_VER} reachable at ${AGENT_IP}:${AGENT_PORT}"
else
    warn "VM Agent not reachable at ${AGENT_IP}:${AGENT_PORT}"
    warn "Start the VM and agent for full analysis capability"
fi

# ─── Ready ────────────────────────────────────────────────

echo ""
echo -e "${BOLD}${GREEN}"
echo "  ══════════════════════════════════════════"
echo "   IsoLens is running!"
echo "  ══════════════════════════════════════════"
echo -e "${NC}"
echo -e "  ${BOLD}Interface${NC}  →  ${CYAN}http://localhost:${INTERFACE_PORT}${NC}"
echo -e "  ${BOLD}Gateway${NC}    →  ${CYAN}http://localhost:${GATEWAY_PORT}${NC}"
echo -e "  ${BOLD}API Docs${NC}   →  ${CYAN}http://localhost:${GATEWAY_PORT}/docs${NC}"
echo ""
echo -e "  Logs: ${YELLOW}gateway.log${NC}  ${YELLOW}interface.log${NC}"
echo -e "  Press ${BOLD}Ctrl+C${NC} to stop all services."
echo ""

# Keep script alive, waiting for child processes
wait
