@echo off
REM ===================================================================
REM  IsoLens VM Setup Script
REM  Run this ONCE inside the sandbox VM (as admin)
REM  Creates directory structure, copies agent, installs auto-start bat
REM ===================================================================

echo ===================================
echo   IsoLens VM Setup
echo ===================================

REM -- Step 1: Ensure Shared Folder access ----------------------------
echo.
echo [Step 1] Ensuring shared folder access...
set "SHARE_ROOT="
if exist Z:\ (
    echo [OK] Z: drive is accessible.
    set "SHARE_ROOT=Z:"
) else (
    net use Z: /delete /y >nul 2>&1
    net use Z: \\VBoxSvr\SandboxShare /persistent:yes >nul 2>&1
    if exist Z:\ (
        echo [OK] Z: drive mapped successfully.
        set "SHARE_ROOT=Z:"
    ) else if exist \\VBoxSvr\SandboxShare\ (
        echo [OK] \\VBoxSvr\SandboxShare is accessible directly.
        set "SHARE_ROOT=\\VBoxSvr\SandboxShare"
    ) else (
        echo [WARN] VirtualBox shared folder not yet mounted. Continuing setup...
        set "SHARE_ROOT=\\VBoxSvr\SandboxShare"
    )
)

REM -- Step 2: Create directory structure -----------------------------
echo.
echo [Step 2] Creating IsoLens directories...
mkdir C:\IsoLens 2>nul
mkdir C:\IsoLens\agent 2>nul
mkdir C:\IsoLens\artifacts 2>nul
mkdir C:\IsoLens\samples 2>nul
echo [OK] Directories created.

REM -- Step 3: Copy agent script --------------------------------------
echo.
echo [Step 3] Copying agent script...
if exist "%~dp0isolens_agent.py" (
    copy /Y "%~dp0isolens_agent.py" C:\IsoLens\agent\isolens_agent.py >nul
) else if exist Z:\isolens_agent.py (
    copy /Y Z:\isolens_agent.py C:\IsoLens\agent\isolens_agent.py >nul
) else if exist \\VBoxSvr\SandboxShare\isolens_agent.py (
    copy /Y \\VBoxSvr\SandboxShare\isolens_agent.py C:\IsoLens\agent\isolens_agent.py >nul
)

if exist C:\IsoLens\agent\isolens_agent.py (
    echo [OK] Agent copied.
) else (
    echo [WARN] isolens_agent.py could not be copied automatically.
)

REM -- Step 4: Verify Python installation -----------------------------
echo.
echo [Step 4] Checking Python installation...
set "PYTHON_PATH=C:\Users\admin\AppData\Local\Python\bin\python.exe"
if not exist "%PYTHON_PATH%" (
    if exist C:\Python312\python.exe set "PYTHON_PATH=C:\Python312\python.exe"
    if exist C:\Python311\python.exe set "PYTHON_PATH=C:\Python311\python.exe"
    if exist C:\Python310\python.exe set "PYTHON_PATH=C:\Python310\python.exe"
)
if not exist "%PYTHON_PATH%" (
    echo [FAIL] Python not found at %PYTHON_PATH%
    echo Install Python from https://www.python.org/downloads/
    echo Make sure to install for the 'admin' user.
    pause
    exit /b 1
)
echo [OK] Python found at %PYTHON_PATH%

REM -- Step 5: Install start_agent.bat --------------------------------
echo.
echo [Step 5] Installing start_agent.bat...
if exist "%~dp0start_agent.bat" (
    copy /Y "%~dp0start_agent.bat" C:\IsoLens\agent\start_agent.bat >nul
) else if exist Z:\start_agent.bat (
    copy /Y Z:\start_agent.bat C:\IsoLens\agent\start_agent.bat >nul
) else if exist \\VBoxSvr\SandboxShare\start_agent.bat (
    copy /Y \\VBoxSvr\SandboxShare\start_agent.bat C:\IsoLens\agent\start_agent.bat >nul
)

REM Fallback generation if start_agent.bat was not in share
if not exist C:\IsoLens\agent\start_agent.bat (
    (
        echo @echo off
        echo title IsoLens Agent
        echo echo ============================================
        echo echo   IsoLens Agent Launcher
        echo echo ============================================
        echo echo.
        echo set "SHARE_PATH="
        echo set RETRIES=0
        echo :CHECK_SHARE
        echo if exist Z:\ ^(
        echo     echo [OK] Z: drive is accessible.
        echo     set "SHARE_PATH=Z:\"
        echo     goto VERIFY_COMPONENTS
        echo ^)
        echo if exist \\VBoxSvr\SandboxShare\ ^(
        echo     echo [OK] \\VBoxSvr\SandboxShare is accessible directly.
        echo     set "SHARE_PATH=\\VBoxSvr\SandboxShare"
        echo     goto VERIFY_COMPONENTS
        echo ^)
        echo echo [*] Attempting to map Z: drive...
        echo net use Z: /delete /y ^>nul 2^>^&1
        echo net use Z: \\VBoxSvr\SandboxShare /persistent:yes ^>nul 2^>^&1
        echo if exist Z:\ ^(
        echo     echo [OK] Z: drive mapped.
        echo     set "SHARE_PATH=Z:\"
        echo     goto VERIFY_COMPONENTS
        echo ^)
        echo if exist \\VBoxSvr\SandboxShare\ ^(
        echo     echo [OK] \\VBoxSvr\SandboxShare is accessible.
        echo     set "SHARE_PATH=\\VBoxSvr\SandboxShare"
        echo     goto VERIFY_COMPONENTS
        echo ^)
        echo set /a RETRIES+=1
        echo if %%RETRIES%% leq 5 ^(
        echo     echo [*] Waiting for shared folder provider ^(attempt %%RETRIES%%/5^)...
        echo     timeout /t 2 /nobreak ^>nul
        echo     goto CHECK_SHARE
        echo ^)
        echo set "SHARE_PATH=\\VBoxSvr\SandboxShare"
        echo :VERIFY_COMPONENTS
        echo set "PYTHON=%PYTHON_PATH%"
        echo cd /d C:\IsoLens
        echo "%%PYTHON%%" C:\IsoLens\agent\isolens_agent.py --host 0.0.0.0 --port 9090 --share "%%SHARE_PATH%%" --workdir C:\IsoLens
    ) > C:\IsoLens\agent\start_agent.bat
)
echo [OK] start_agent.bat ready.

REM -- Step 6: Install to Startup folder for auto-start ---------------
echo.
echo [Step 6] Installing auto-start bat to Startup folder...
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
copy /Y C:\IsoLens\agent\start_agent.bat "%STARTUP%\isolens_agent.bat" >nul
if errorlevel 1 (
    echo [WARN] Could not copy to Startup folder.
) else (
    echo [OK] Agent will auto-start on login.
)

REM -- Step 7: Copy malware emulator (optional) -----------------------
echo.
echo [Step 7] Copying malware emulator (if available)...
if exist "%~dp0malware_emulator.cs" (
    copy /Y "%~dp0malware_emulator.cs" C:\IsoLens\samples\malware_emulator.cs >nul
    echo [OK] malware_emulator.cs copied.
) else if exist Z:\malware_emulator.cs (
    copy /Y Z:\malware_emulator.cs C:\IsoLens\samples\malware_emulator.cs >nul
    echo [OK] malware_emulator.cs copied.
) else if exist \\VBoxSvr\SandboxShare\malware_emulator.cs (
    copy /Y \\VBoxSvr\SandboxShare\malware_emulator.cs C:\IsoLens\samples\malware_emulator.cs >nul
    echo [OK] malware_emulator.cs copied.
)

echo.
echo ===================================
echo   Setup Complete!
echo ===================================
echo.
echo Agent location:  C:\IsoLens\agent\isolens_agent.py
echo Launcher:        C:\IsoLens\agent\start_agent.bat
echo Auto-start:      %STARTUP%\isolens_agent.bat
