@echo off
REM ===================================================================
REM  IsoLens VM Setup Script
REM  Run this ONCE from Z:\ inside the sandbox VM (as admin)
REM  Creates directory structure, copies agent, installs auto-start bat
REM ===================================================================

echo ===================================
echo   IsoLens VM Setup
echo ===================================

REM -- Step 1: Map Z: drive if needed ---------------------------------
echo.
echo [Step 1] Ensuring Z: drive is mapped...
if not exist Z:\ (
    net use Z: \\VBoxSvr\SandboxShare /persistent:yes
    if errorlevel 1 (
        echo [FAIL] Could not map Z: drive. Make sure Shared Folder is configured in VirtualBox.
        pause
        exit /b 1
    )
)
echo [OK] Z: drive available.

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
copy /Y Z:\isolens_agent.py C:\IsoLens\agent\isolens_agent.py
if errorlevel 1 (
    echo [FAIL] Could not copy isolens_agent.py from Z:\
    echo Make sure isolens_agent.py is in the SandboxShare folder.
    pause
    exit /b 1
)
echo [OK] Agent copied.

REM -- Step 4: Verify Python installation -----------------------------
echo.
echo [Step 4] Checking Python installation...
set "PYTHON_PATH=C:\Users\admin\AppData\Local\Python\bin\python.exe"
if not exist "%PYTHON_PATH%" (
    echo [FAIL] Python not found at %PYTHON_PATH%
    echo Install Python from https://www.python.org/downloads/
    echo Make sure to install for the 'admin' user.
    pause
    exit /b 1
)
echo [OK] Python found at %PYTHON_PATH%

REM -- Step 5: Generate start_agent.bat with FULL Python path ---------
REM   IMPORTANT: Do NOT use bare 'python' — the Windows Store stub
REM   (WindowsApps\python.exe) is found first in PATH and silently fails.
REM   IMPORTANT: Do NOT use Z:\ with trailing backslash in --share arg.
REM   Windows C runtime parses \<space> as escape, mangling arguments.
echo.
echo [Step 5] Generating start_agent.bat...
(
    echo @echo off
    echo title IsoLens Agent
    echo echo ============================================
    echo echo   IsoLens Agent Launcher
    echo echo ============================================
    echo echo.
    echo if not exist Z:\ ^(
    echo     echo [*] Mapping Z: drive...
    echo     net use Z: \\VBoxSvr\SandboxShare /persistent:yes
    echo     if errorlevel 1 ^(
    echo         echo [FAIL] Could not map Z: drive.
    echo         pause
    echo         exit /b 1
    echo     ^)
    echo     timeout /t 2 /nobreak ^>nul
    echo ^)
    echo set "PYTHON=%PYTHON_PATH%"
    echo if not exist "%%PYTHON%%" ^(
    echo     echo [FAIL] Python not found
    echo     pause
    echo     exit /b 1
    echo ^)
    echo echo [OK] Python : %%PYTHON%%
    echo echo [OK] Share  : Z:
    echo echo [*] Starting agent on port 9090...
    echo echo.
    echo cd /d C:\IsoLens
    echo "%%PYTHON%%" C:\IsoLens\agent\isolens_agent.py --host 0.0.0.0 --port 9090 --share Z: --workdir C:\IsoLens
    echo echo.
    echo echo [!] Agent exited unexpectedly.
    echo pause
) > C:\IsoLens\agent\start_agent.bat
echo [OK] start_agent.bat created.

REM -- Step 6: Install to Startup folder for auto-start ---------------
echo.
echo [Step 6] Installing auto-start bat to Startup folder...
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
copy /Y C:\IsoLens\agent\start_agent.bat "%STARTUP%\isolens_agent.bat"
if errorlevel 1 (
    echo [WARN] Could not copy to Startup folder.
) else (
    echo [OK] Agent will auto-start on login.
)

REM -- Step 7: Copy malware emulator (optional) -----------------------
echo.
echo [Step 7] Copying malware emulator (if available)...
if exist Z:\malware_emulator.cs (
    copy /Y Z:\malware_emulator.cs C:\IsoLens\samples\malware_emulator.cs
    echo [OK] malware_emulator.cs copied.
) else (
    echo [SKIP] malware_emulator.cs not found in Z:\
)
if exist Z:\build_emulator.bat (
    copy /Y Z:\build_emulator.bat C:\IsoLens\samples\build_emulator.bat
    echo [OK] build_emulator.bat copied.
) else (
    echo [SKIP] build_emulator.bat not found in Z:\
)

echo.
echo ===================================
echo   Setup Complete!
echo ===================================
echo.
echo Agent location:  C:\IsoLens\agent\isolens_agent.py
echo Launcher:        C:\IsoLens\agent\start_agent.bat
echo Auto-start:      %STARTUP%\isolens_agent.bat
echo Python:          %PYTHON_PATH%
echo.
echo To test now, run:  C:\IsoLens\agent\start_agent.bat
echo Or reboot to verify auto-start works.
echo.
pause
