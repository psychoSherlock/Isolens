$batContent = @"
@echo off
title IsoLens Agent
echo ============================================
echo   IsoLens Agent Launcher (Auto-Recovery)
echo ============================================
echo.

REM Ensure linked connections are enabled for split-token admin sessions
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableLinkedConnections /t REG_DWORD /d 1 /f >nul 2>&1

:CHECK_SHARE
set "SHARE_PATH="
set RETRIES=0

:RETRY_LOOP
REM 1. Check if Z:\ is already accessible
if exist Z:\ (
    echo [OK] Z: drive is accessible.
    set "SHARE_PATH=Z:\"
    goto VERIFY_COMPONENTS
)

REM 2. Attempt mapping Z: drive to \\VBoxSvr\SandboxShare
echo [*] Attempting to map Z: drive to \\VBoxSvr\SandboxShare...
net use Z: \\VBoxSvr\SandboxShare /persistent:yes >nul 2>&1
if exist Z:\ (
    echo [OK] Z: drive mapped successfully.
    set "SHARE_PATH=Z:\"
    goto VERIFY_COMPONENTS
)

REM 3. If Z: returned conflict or stale session, delete and remap
net use Z: /delete /y >nul 2>&1
net use Z: \\VBoxSvr\SandboxShare /persistent:yes >nul 2>&1
if exist Z:\ (
    echo [OK] Z: drive mapped after refresh.
    set "SHARE_PATH=Z:\"
    goto VERIFY_COMPONENTS
)

REM 4. Fallback: try Y: drive if Z: is occupied or locked
net use Y: \\VBoxSvr\SandboxShare /persistent:yes >nul 2>&1
if exist Y:\ (
    echo [OK] Y: drive mapped as fallback shared folder.
    set "SHARE_PATH=Y:\"
    goto VERIFY_COMPONENTS
)

REM 5. Retry loop (wait for VirtualBox Shared Folder provider to initialize)
set /a RETRIES+=1
if %RETRIES% leq 15 (
    echo [*] Waiting for VirtualBox shared folders (attempt %RETRIES%/15)...
    ping -n 3 127.0.0.1 >nul
    goto RETRY_LOOP
)

REM 6. Last resort fallback to Z:\ (agent internal auto-connector will retry)
echo [WARN] Could not verify shared folder drive after 15 attempts.
echo [*] Launching agent with Z:\ default; agent will auto-reconnect on-demand...
set "SHARE_PATH=Z:\"

:VERIFY_COMPONENTS
REM -- Verify Python exists --
set "PYTHON=C:\Users\admin\AppData\Local\Python\bin\python.exe"
if not exist "%PYTHON%" (
    if exist C:\Python312\python.exe set "PYTHON=C:\Python312\python.exe"
    if exist C:\Python311\python.exe set "PYTHON=C:\Python311\python.exe"
    if exist C:\Python310\python.exe set "PYTHON=C:\Python310\python.exe"
)
if not exist "%PYTHON%" (
    echo [FAIL] Python not found at %PYTHON%
    ping -n 6 127.0.0.1 >nul
    exit /b 1
)

REM -- Always sync latest agent script from share if available --
if exist "%SHARE_PATH%isolens_agent.py" (
    echo [*] Syncing latest isolens_agent.py from share...
    copy /Y "%SHARE_PATH%isolens_agent.py" C:\IsoLens\agent\isolens_agent.py >nul
) else if exist Z:\isolens_agent.py (
    copy /Y Z:\isolens_agent.py C:\IsoLens\agent\isolens_agent.py >nul
)

if not exist C:\IsoLens\agent\isolens_agent.py (
    echo [FAIL] isolens_agent.py not found in C:\IsoLens\agent\
    ping -n 4 127.0.0.1 >nul
    goto RETRY_LOOP
)

echo [OK] Python : %PYTHON%
echo [OK] Share  : %SHARE_PATH%
echo [OK] Workdir: C:\IsoLens
echo [*] Starting agent on port 9090...
echo.

cd /d C:\IsoLens
"%PYTHON%" C:\IsoLens\agent\isolens_agent.py --host 0.0.0.0 --port 9090 --share "%SHARE_PATH%" --workdir C:\IsoLens

echo.
echo [!] Agent exited. Re-checking share and restarting in 3 seconds...
ping -n 4 127.0.0.1 >nul
goto CHECK_SHARE
"@

# Deploy bat to both locations
Set-Content -Path "C:\IsoLens\agent\start_agent.bat" -Value $batContent -Encoding ASCII
Copy-Item "C:\IsoLens\agent\start_agent.bat" "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\isolens_agent.bat" -Force

# Also copy updated agent from shared folder if available
if (Test-Path "Z:\isolens_agent.py") {
    Copy-Item "Z:\isolens_agent.py" "C:\IsoLens\agent\isolens_agent.py" -Force
    Write-Host "[OK] Agent script updated from Z:\isolens_agent.py"
} elseif (Test-Path "\\VBoxSvr\SandboxShare\isolens_agent.py") {
    Copy-Item "\\VBoxSvr\SandboxShare\isolens_agent.py" "C:\IsoLens\agent\isolens_agent.py" -Force
    Write-Host "[OK] Agent script updated from \\VBoxSvr\SandboxShare\isolens_agent.py"
}

Write-Host "=== Deployed to both locations ==="
Write-Host "1) C:\IsoLens\agent\start_agent.bat"
Write-Host "2) $env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\isolens_agent.bat"
