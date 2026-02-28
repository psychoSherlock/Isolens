$batContent = @"
@echo off
title IsoLens Agent
echo ============================================
echo   IsoLens Agent Launcher
echo ============================================
echo.

REM -- Map Z: drive if not yet available --
if not exist Z:\ (
    echo [*] Mapping Z: drive...
    net use Z: \\VBoxSvr\SandboxShare /persistent:yes
    if errorlevel 1 (
        echo [FAIL] Could not map Z: drive.
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
)

REM -- Verify Python exists --
REM   IMPORTANT: Use FULL path, no quotes (path has no spaces).
REM   Do NOT use bare 'python' - Windows Store stub is found first.
set PYTHON=C:\Users\admin\AppData\Local\Python\bin\python.exe
if not exist %PYTHON% (
    echo [FAIL] Python not found at %PYTHON%
    pause
    exit /b 1
)

REM -- Verify agent script exists --
if not exist C:\IsoLens\agent\isolens_agent.py (
    echo [FAIL] isolens_agent.py not found
    pause
    exit /b 1
)

echo [OK] Python : %PYTHON%
echo [OK] Share  : Z:
echo [OK] Workdir: C:\IsoLens
echo [*] Starting agent on port 9090...
echo.

cd /d C:\IsoLens
%PYTHON% C:\IsoLens\agent\isolens_agent.py --host 0.0.0.0 --port 9090 --share Z: --workdir C:\IsoLens

echo.
echo [!] Agent exited unexpectedly.
pause
"@

# Deploy bat to both locations
Set-Content -Path "C:\IsoLens\agent\start_agent.bat" -Value $batContent -Encoding ASCII
Copy-Item "C:\IsoLens\agent\start_agent.bat" "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\isolens_agent.bat" -Force

# Also copy updated agent from shared folder if available
if (Test-Path "Z:\isolens_agent.py") {
    Copy-Item "Z:\isolens_agent.py" "C:\IsoLens\agent\isolens_agent.py" -Force
    Write-Host "[OK] Agent script updated from Z:\isolens_agent.py"
}

Write-Host "=== Deployed to both locations ==="
Write-Host "1) C:\IsoLens\agent\start_agent.bat"
Write-Host "2) $env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\isolens_agent.bat"
