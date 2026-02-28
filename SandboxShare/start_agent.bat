@echo off
REM ── IsoLens Agent Launcher ──────────────────────────────────
REM This script is called by the "IsoLensAgent" scheduled task.
REM It ensures the working directory, shared-folder drive, and
REM Python path are all correct before launching the agent.
REM ─────────────────────────────────────────────────────────────

set PYTHON=C:\Users\admin\AppData\Local\Python\bin\python.exe
set AGENT=C:\IsoLens\agent\isolens_agent.py
set WORKDIR=C:\IsoLens
set SHARE=Z:\
set HOST=0.0.0.0
set PORT=9090
set LOGFILE=C:\IsoLens\agent_log.txt

REM Map shared folder drive if not already mapped
if not exist Z:\ (
    net use Z: \\VBoxSvr\SandboxShare /persistent:yes >nul 2>&1
)

REM Ensure workdir exists
if not exist "%WORKDIR%" mkdir "%WORKDIR%"

cd /d "%WORKDIR%"

REM Start the agent, redirecting output to a log file
"%PYTHON%" "%AGENT%" --host %HOST% --port %PORT% --share "%SHARE%" --workdir "%WORKDIR%" >> "%LOGFILE%" 2>&1
