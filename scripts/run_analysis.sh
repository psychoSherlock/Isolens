#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
#  IsoLens Analysis Runner
#
#  Submits a sample file to the IsoLens gateway, monitors progress
#  in real-time, and tells you where the report was collected.
#
#  Usage:
#    ./scripts/run_analysis.sh <sample_file> [timeout_seconds]
#
#  Examples:
#    ./scripts/run_analysis.sh SandboxShare/malware_emulator.exe
#    ./scripts/run_analysis.sh /tmp/suspicious.exe 90
# ──────────────────────────────────────────────────────────────

set -euo pipefail

# ── Config ────────────────────────────────────────────────────
GATEWAY="http://127.0.0.1:6969"
POLL_INTERVAL=5          # seconds between status polls
DEFAULT_TIMEOUT=60       # default execution timeout

# ── Colors ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# ── Helpers ───────────────────────────────────────────────────
info()  { echo -e "${CYAN}[*]${RESET} $*"; }
ok()    { echo -e "${GREEN}[✓]${RESET} $*"; }
warn()  { echo -e "${YELLOW}[!]${RESET} $*"; }
fail()  { echo -e "${RED}[✗]${RESET} $*"; }
step()  { echo -e "${BOLD}${CYAN}───${RESET} $* ${CYAN}───${RESET}"; }
dim()   { echo -e "${DIM}    $*${RESET}"; }

# ── Arg parsing ───────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
    echo -e "${BOLD}Usage:${RESET} $0 <sample_file> [timeout_seconds]"
    echo ""
    echo "  sample_file       Path to the file to analyse"
    echo "  timeout_seconds   How long the agent waits after execution (default: $DEFAULT_TIMEOUT)"
    exit 1
fi

SAMPLE_FILE="$1"
TIMEOUT="${2:-$DEFAULT_TIMEOUT}"

if [[ ! -f "$SAMPLE_FILE" ]]; then
    fail "File not found: $SAMPLE_FILE"
    exit 1
fi

SAMPLE_NAME=$(basename "$SAMPLE_FILE")
SAMPLE_SIZE=$(du -h "$SAMPLE_FILE" | cut -f1)

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║           IsoLens Analysis Runner                ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${RESET}"
echo ""
info "Sample:  ${BOLD}$SAMPLE_NAME${RESET} ($SAMPLE_SIZE)"
info "Timeout: ${BOLD}${TIMEOUT}s${RESET}"
info "Gateway: ${BOLD}$GATEWAY${RESET}"
echo ""

# ── Step 1: Gateway health ────────────────────────────────────
step "Step 1/6: Checking gateway"

PING=$(curl -s --max-time 5 "$GATEWAY/api/ping" 2>/dev/null || echo "")
if echo "$PING" | grep -q '"pong"'; then
    ok "Gateway is alive"
else
    fail "Gateway not reachable at $GATEWAY"
    dim "Start it with: uvicorn core.gateway.app:app --host 0.0.0.0 --port 6969"
    exit 1
fi

# ── Step 2: VM & agent readiness ──────────────────────────────
step "Step 2/6: Checking VM & agent readiness"

CHECK=$(curl -s --max-time 15 -X POST "$GATEWAY/api/analysis/check-vm" 2>/dev/null || echo "")
AGENT_OK=$(echo "$CHECK" | python3 -c "import sys,json; d=json.load(sys.stdin).get('data',{}); print(d.get('agent_reachable',False))" 2>/dev/null || echo "False")
READY=$(echo "$CHECK" | python3 -c "import sys,json; d=json.load(sys.stdin).get('data',{}); print(d.get('ready',False))" 2>/dev/null || echo "False")

if [[ "$AGENT_OK" == "True" ]]; then
    ok "Agent is reachable"
else
    fail "Agent is not reachable inside the VM"
    dim "Make sure the VM is running and the agent is started."
    exit 1
fi

# Show collector status
echo "$CHECK" | python3 -c "
import sys, json
data = json.load(sys.stdin).get('data', {})
collectors = {k: v for k, v in data.items() if k.startswith('collector_')}
for name, avail in sorted(collectors.items()):
    tag = '✓' if avail else '✗'
    label = name.replace('collector_', '')
    print(f'    {tag} {label}')
" 2>/dev/null

if [[ "$READY" == "True" ]]; then
    ok "System is ready for analysis"
else
    warn "System reports not fully ready — proceeding anyway"
fi

# ── Step 3: Cleanup previous artifacts ────────────────────────
step "Step 3/6: Cleaning up previous artifacts"

CLEANUP=$(curl -s --max-time 15 -X POST "$GATEWAY/api/analysis/cleanup" 2>/dev/null || echo "")
CLEANUP_OK=$(echo "$CLEANUP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
if [[ "$CLEANUP_OK" == "ok" ]]; then
    ok "Agent artifacts cleaned"
else
    warn "Cleanup returned: $CLEANUP_OK (continuing anyway)"
fi

# ── Step 4: Submit the sample ─────────────────────────────────
step "Step 4/6: Submitting sample for analysis"

info "Uploading ${BOLD}$SAMPLE_NAME${RESET} and starting execution..."
info "The agent will execute the sample and wait ${BOLD}${TIMEOUT}s${RESET} for behavior."
echo ""

# Submit is blocking on the gateway side — it will take a while.
# We run it in background and poll the agent status for live updates.

RESULT_FILE=$(mktemp /tmp/isolens_result_XXXXXX.json)

curl -s -X POST "$GATEWAY/api/analysis/submit" \
    -F "file=@$SAMPLE_FILE" \
    -F "timeout=$TIMEOUT" \
    --max-time 900 \
    -o "$RESULT_FILE" 2>/dev/null &

CURL_PID=$!

# ── Step 5: Live progress polling ─────────────────────────────
step "Step 5/6: Monitoring progress"

LAST_STATUS=""
SPINNER_CHARS="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
SPIN_IDX=0
ELAPSED=0

while kill -0 "$CURL_PID" 2>/dev/null; do
    # Get agent status via gateway proxy
    AGENT_JSON=$(curl -s --max-time 5 "$GATEWAY/api/analysis/agent/status" 2>/dev/null || echo "")
    STATUS=$(echo "$AGENT_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('status','unknown'))" 2>/dev/null || echo "unknown")
    SAMPLE=$(echo "$AGENT_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('current_sample',''))" 2>/dev/null || echo "")

    SPIN_CHAR="${SPINNER_CHARS:$SPIN_IDX:1}"
    SPIN_IDX=$(( (SPIN_IDX + 1) % ${#SPINNER_CHARS} ))

    # Print status change
    if [[ "$STATUS" != "$LAST_STATUS" ]]; then
        case "$STATUS" in
            idle)
                [[ -n "$LAST_STATUS" ]] && ok "Agent is idle (${ELAPSED}s elapsed)"
                ;;
            executing)
                info "Agent is ${BOLD}executing${RESET} ${YELLOW}$SAMPLE${RESET}... (waiting ${TIMEOUT}s)"
                ;;
            collecting)
                ok "Execution phase done (${ELAPSED}s elapsed)"
                info "Agent is ${BOLD}collecting artifacts${RESET}..."
                ;;
            error)
                fail "Agent reported an error"
                ;;
            *)
                info "Agent status: $STATUS"
                ;;
        esac
        LAST_STATUS="$STATUS"
    else
        # Inline spinner for same status
        printf "\r${DIM}    %s  %s — %ds elapsed${RESET}  " "$SPIN_CHAR" "$STATUS" "$ELAPSED"
    fi

    sleep "$POLL_INTERVAL"
    ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

# Clear the spinner line
printf "\r%80s\r" ""

wait "$CURL_PID" || true

# ── Step 6: Results ───────────────────────────────────────────
step "Step 6/6: Results"

if [[ ! -s "$RESULT_FILE" ]]; then
    fail "No response received from gateway"
    rm -f "$RESULT_FILE"
    exit 1
fi

# Parse the result
ANALYSIS_STATUS=$(python3 -c "
import json, sys
with open('$RESULT_FILE') as f:
    resp = json.load(f)
data = resp.get('data', {})
status = data.get('status', 'unknown')
print(status)
" 2>/dev/null || echo "unknown")

if [[ "$ANALYSIS_STATUS" == "complete" ]]; then
    echo ""
    ok "${BOLD}Analysis completed successfully!${RESET}"
    echo ""

    # Extract details
    python3 -c "
import json
with open('$RESULT_FILE') as f:
    resp = json.load(f)
data = resp.get('data', {})

print('  ┌─────────────────────────────────────────────')
print(f'  │ Analysis ID:   {data.get(\"analysis_id\", \"?\")}')
print(f'  │ Sample:        {data.get(\"sample_name\", \"?\")}')
print(f'  │ Status:        {data.get(\"status\", \"?\")}')
print(f'  │ Started:       {data.get(\"started_at\", \"?\")}')
print(f'  │ Completed:     {data.get(\"completed_at\", \"?\")}')
print(f'  │ Sysmon Events: {data.get(\"sysmon_events\", 0)}')
print(f'  │ Files:         {len(data.get(\"files_collected\", []))}')
for f in data.get('files_collected', []):
    print(f'  │   • {f}')
print(f'  │ Agent Package: {data.get(\"agent_package\", \"none\")}')
print(f'  │ Report Dir:    {data.get(\"report_dir\", \"?\")}')
print('  └─────────────────────────────────────────────')
" 2>/dev/null

    REPORT_DIR=$(python3 -c "
import json
with open('$RESULT_FILE') as f:
    print(json.load(f).get('data',{}).get('report_dir',''))
" 2>/dev/null)

    echo ""
    echo -e "${GREEN}${BOLD}  ╔══════════════════════════════════════════════════╗${RESET}"
    echo -e "${GREEN}${BOLD}  ║  Reports collected at:                           ║${RESET}"
    echo -e "${GREEN}${BOLD}  ║  $REPORT_DIR${RESET}"
    echo -e "${GREEN}${BOLD}  ╚══════════════════════════════════════════════════╝${RESET}"
    echo ""

    if [[ -d "$REPORT_DIR" ]]; then
        info "Contents:"
        find "$REPORT_DIR" -type f -printf "    %s\t%P\n" 2>/dev/null | \
            awk '{ 
                size=$1;
                if (size > 1073741824) printf "    %5.1f GB  %s\n", size/1073741824, $2;
                else if (size > 1048576) printf "    %5.1f MB  %s\n", size/1048576, $2;
                else if (size > 1024) printf "    %5.1f KB  %s\n", size/1024, $2;
                else printf "    %5d B   %s\n", size, $2;
            }' | sort
    fi

elif [[ "$ANALYSIS_STATUS" == "failed" ]]; then
    fail "Analysis failed"
    ERROR=$(python3 -c "
import json
with open('$RESULT_FILE') as f:
    data = json.load(f).get('data', {})
    print(data.get('error', 'Unknown error'))
" 2>/dev/null)
    dim "Error: $ERROR"
else
    warn "Unexpected analysis status: $ANALYSIS_STATUS"
    dim "Raw response:"
    cat "$RESULT_FILE" | python3 -m json.tool 2>/dev/null || cat "$RESULT_FILE"
fi

rm -f "$RESULT_FILE"
echo ""
