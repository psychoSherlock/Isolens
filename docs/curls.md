# IsoLens Gateway Curl Guide

Short descriptions with example curl commands for all endpoints.

Defaults used in these examples:

- `dry_run=false`
- `raise_on_error=true`

## Ping

Health check for the gateway.

```bash
curl -s http://127.0.0.1:6969/api/ping
```

## Version

Return the current gateway version.

```bash
curl -s http://127.0.0.1:6969/api/version
```

## List VMs

List all registered VirtualBox VMs.

```bash
curl -s "http://127.0.0.1:6969/api/vms?dry_run=false&raise_on_error=true"
```

## List Running VMs

List currently running VMs.

```bash
curl -s "http://127.0.0.1:6969/api/vms/running?dry_run=false&raise_on_error=true"
```

## VM IP Addresses

Retrieve all network interface IPs for a given VM via VirtualBox Guest Additions.
The VM name is passed as a query parameter. Requires Guest Additions to be running inside the VM.

```bash
curl -s "http://127.0.0.1:6969/api/vms/ip?vm=WindowsSandbox&dry_run=false&raise_on_error=true"
```

## VM Info

Show information about a VM.

```bash
curl -s -X POST http://127.0.0.1:6969/api/vms/info \
  -H 'Content-Type: application/json' \
  -d '{"vm":"WindowsSandbox","machinereadable":true,"dry_run":false,"raise_on_error":true}'
```

## Start VM

Start a VM (optionally headless).

```bash
curl -s -X POST http://127.0.0.1:6969/api/vms/start \
  -H 'Content-Type: application/json' \
  -d '{"vm":"WindowsSandbox","headless":true,"dry_run":false,"raise_on_error":true}'
```

## Power Off VM

Force power off a VM.

```bash
curl -s -X POST http://127.0.0.1:6969/api/vms/poweroff \
  -H 'Content-Type: application/json' \
  -d '{"vm":"WindowsSandbox","dry_run":false,"raise_on_error":true}'
```

## Save State

Save VM state to disk.

```bash
curl -s -X POST http://127.0.0.1:6969/api/vms/savestate \
  -H 'Content-Type: application/json' \
  -d '{"vm":"WindowsSandbox","dry_run":false,"raise_on_error":true}'
```

## Pause VM

Pause VM execution.

```bash
curl -s -X POST http://127.0.0.1:6969/api/vms/pause \
  -H 'Content-Type: application/json' \
  -d '{"vm":"WindowsSandbox","dry_run":false,"raise_on_error":true}'
```

## Resume VM

Resume a paused VM.

```bash
curl -s -X POST http://127.0.0.1:6969/api/vms/resume \
  -H 'Content-Type: application/json' \
  -d '{"vm":"WindowsSandbox","dry_run":false,"raise_on_error":true}'
```

## Reset VM

Hard reset a VM.

```bash
curl -s -X POST http://127.0.0.1:6969/api/vms/reset \
  -H 'Content-Type: application/json' \
  -d '{"vm":"WindowsSandbox","dry_run":false,"raise_on_error":true}'
```

## Shutdown VM

Graceful shutdown (use `force=true` for forced shutdown).

```bash
curl -s -X POST "http://127.0.0.1:6969/api/vms/shutdown?force=false" \
  -H 'Content-Type: application/json' \
  -d '{"vm":"WindowsSandbox","dry_run":false,"raise_on_error":true}'
```

## Snapshot Take

Create a snapshot for a VM.

```bash
curl -s -X POST http://127.0.0.1:6969/api/vms/snapshot/take \
  -H 'Content-Type: application/json' \
  -d '{"vm":"WindowsSandbox","name":"Baseline","dry_run":false,"raise_on_error":true}'
```

## Snapshot Restore

Restore a named snapshot.

```bash
curl -s -X POST http://127.0.0.1:6969/api/vms/snapshot/restore \
  -H 'Content-Type: application/json' \
  -d '{"vm":"WindowsSandbox","name":"Baseline","dry_run":false,"raise_on_error":true}'
```

## Snapshot Restore Current

Restore the current snapshot.

```bash
curl -s -X POST http://127.0.0.1:6969/api/vms/snapshot/restore-current \
  -H 'Content-Type: application/json' \
  -d '{"vm":"WindowsSandbox","dry_run":false,"raise_on_error":true}'
```

---

# Analysis Endpoints

Endpoints under `/api/analysis/` coordinate the full sandbox analysis
pipeline. The gateway orchestrator talks to the in-VM agent over HTTP and
uses the VirtualBox shared folder for file transfer.

## Submit Analysis

Upload a sample and start the full analysis pipeline. The orchestrator
copies the sample to `SandboxShare/`, tells the agent to execute it,
takes VBoxManage screenshots during execution, polls until complete,
and retrieves the results zip.

The `screenshot_interval` parameter controls how often (in seconds) a
screenshot of the VM display is captured (default: 5).

```bash
curl -s -X POST http://127.0.0.1:6969/api/analysis/submit \
  -F "file=@/path/to/sample.exe" \
  -F "timeout=60" \
  -F "screenshot_interval=5"
```

## Analysis Status

Return the current or most recent analysis result.

```bash
curl -s http://127.0.0.1:6969/api/analysis/status
```

## Check VM Readiness

Verify the sandbox agent is reachable, required tools are available, and
the shared folder exists on the host.

```bash
curl -s -X POST http://127.0.0.1:6969/api/analysis/check-vm
```

## Cleanup Agent Artifacts

Ask the agent to remove all collected artifacts.

```bash
curl -s -X POST http://127.0.0.1:6969/api/analysis/cleanup
```

## Agent Status (Proxy)

Proxy to the in-VM agent's `/api/status` endpoint.

```bash
curl -s http://127.0.0.1:6969/api/analysis/agent/status
```

## Agent Collectors (Proxy)

Proxy to the in-VM agent's `/api/collectors` endpoint.

```bash
curl -s http://127.0.0.1:6969/api/analysis/agent/collectors
```

## Agent Artifacts (Proxy)

Proxy to the in-VM agent's `/api/artifacts` endpoint.

```bash
curl -s http://127.0.0.1:6969/api/analysis/agent/artifacts
```

---

# Guest Agent Endpoints

The following endpoints are served by `isolens_agent.py` running **inside** the sandbox VM.
Default address: `http://<vm-host-only-ip>:9090`.

## Agent Status

Health check and current agent state.

```bash
curl -s http://192.168.56.105:9090/api/status
```

## List Collectors

List available artifact collectors and their availability.

```bash
curl -s http://192.168.56.105:9090/api/collectors
```

## List Artifacts

List collected artifact files.

```bash
curl -s http://192.168.56.105:9090/api/artifacts
```

## Execute Sample

Execute a sample file placed in the shared folder. Runs in the background.

```bash
curl -s -X POST http://192.168.56.105:9090/api/execute \
  -H 'Content-Type: application/json' \
  -d '{"filename":"sample.exe","timeout":60}'
```

## Collect Artifacts

Run all collectors without executing a sample.

```bash
curl -s -X POST http://192.168.56.105:9090/api/collect
```

## Cleanup Artifacts

Remove all collected artifacts from the working directory.

```bash
curl -s -X POST http://192.168.56.105:9090/api/cleanup
```

## Shutdown Agent

Gracefully shut down the agent service.

```bash
curl -s -X POST http://192.168.56.105:9090/api/shutdown
```

---

# Gateway Report / Screenshot Endpoints

## List Screenshots

List screenshot files for a given analysis.

```bash
curl -s http://127.0.0.1:6969/api/analysis/report/ANALYSIS_ID/screenshots
```

## Serve Report File

Serve a file from the analysis report directory (e.g. a screenshot PNG).

```bash
curl -s http://127.0.0.1:6969/api/analysis/report/ANALYSIS_ID/file/screenshots/screenshot_001.png --output screenshot.png
```

## List All Reports

List all analysis reports with saved manifests.

```bash
curl -s http://127.0.0.1:6969/api/analysis/reports/list
```

## Clear All Reports

Delete all analysis reports, artifacts, and associated data. Also removes
result zip files from SandboxShare.

```bash
curl -s -X DELETE http://127.0.0.1:6969/api/analysis/reports/clear
```

## Live VM Screenshot

Capture and serve a live PNG screenshot of the VM display. Returns the raw
PNG image. The VM must be running.

```bash
curl -s "http://127.0.0.1:6969/api/vms/screen?vm=WindowsSandbox" --output live_screen.png
```

## Get Full Report Data

Retrieve all parsed collector data for a single analysis (Sysmon, Procmon, Network, Handle, Tcpvcon, screenshots) in one response.

```bash
curl -s http://127.0.0.1:6969/api/analysis/report/ANALYSIS_ID/data
```

## Run AI Threat Analysis

Run the multi-agent AI threat analysis pipeline on an existing report. Each collector's data is sent to a specialised Copilot agent (gpt-5-mini), then all per-tool XML analyses are fed to the threat-summarizer agent for a final risk score and executive summary. Results are saved to `<report_dir>/ai_analysis/`.

```bash
curl -s -X POST http://127.0.0.1:6969/api/analysis/report/ANALYSIS_ID/ai-analyze
```

## Get AI Report

Retrieve a previously generated AI threat analysis report (JSON).

```bash
curl -s http://127.0.0.1:6969/api/analysis/report/ANALYSIS_ID/ai-report
```
