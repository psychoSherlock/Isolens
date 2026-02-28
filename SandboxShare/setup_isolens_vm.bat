@echo off
REM ================================================================
REM  IsoLens VM Setup Script — Run as Administrator inside the VM
REM  This script: fixes firewall, starts SSH, deploys agent,
REM  sets up auto-start for agent and Procmon.
REM ================================================================

echo.
echo ========================================
echo   IsoLens VM Setup
echo ========================================
echo.

REM --- 1. Fix Firewall ---
echo [1/7] Configuring firewall rules...
netsh advfirewall firewall add rule name="IsoLens SSH" dir=in action=allow protocol=TCP localport=22 >NUL 2>&1
netsh advfirewall firewall add rule name="IsoLens Agent" dir=in action=allow protocol=TCP localport=9090 >NUL 2>&1
netsh advfirewall firewall add rule name="Allow ICMPv4" protocol=icmpv4:8,any dir=in action=allow >NUL 2>&1
echo    Firewall rules added (SSH:22, Agent:9090, ICMP)

REM --- 2. Start SSH ---
echo [2/7] Starting SSH service...
sc config sshd start= auto >NUL 2>&1
net start sshd >NUL 2>&1
echo    sshd configured for auto-start

REM --- 3. Check Python ---
echo [3/7] Checking Python...
python --version 2>&1
where python 2>&1
if errorlevel 1 (
    echo    ERROR: Python not found! Install Python first.
    pause
    exit /b 1
)

REM --- 4. Deploy Agent ---
echo [4/7] Deploying agent to C:\IsoLens\agent\...
if not exist "C:\IsoLens\agent" mkdir "C:\IsoLens\agent"
copy /Y "Z:\isolens_agent.py" "C:\IsoLens\agent\isolens_agent.py" >NUL
if exist "C:\IsoLens\agent\isolens_agent.py" (
    echo    Agent deployed successfully
) else (
    echo    ERROR: Failed to copy agent from Z:\
    echo    Make sure the shared folder Z: is mapped
    pause
    exit /b 1
)

REM --- 5. Create agent startup batch ---
echo [5/7] Creating agent auto-start...
(
echo @echo off
echo cd /d C:\IsoLens\agent
echo python isolens_agent.py --host 0.0.0.0 --port 9090 --share "Z:\" --workdir "C:\IsoLens"
) > "C:\IsoLens\agent\start_agent.bat"

REM Add to Startup folder (runs on login)
copy /Y "C:\IsoLens\agent\start_agent.bat" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\isolens_agent.bat" >NUL
echo    Agent auto-start configured (Startup folder)

REM --- 6. Create Procmon startup ---
echo [6/7] Creating Procmon auto-start...
if exist "C:\IsoLens\tools\Procmon64.exe" (
    REM Procmon in quiet background mode: logs to backing file, no GUI
    (
    echo @echo off
    echo cd /d C:\IsoLens\tools
    echo start "" /B Procmon64.exe /AcceptEula /Quiet /Minimized /BackingFile C:\IsoLens\artifacts\procmon\procmon.pml
    ) > "C:\IsoLens\tools\start_procmon.bat"
    copy /Y "C:\IsoLens\tools\start_procmon.bat" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\isolens_procmon.bat" >NUL
    echo    Procmon auto-start configured
) else (
    echo    Procmon64.exe not found at C:\IsoLens\tools\ — skipping
)

REM --- 7. Start agent NOW ---
echo [7/7] Starting agent now...
if not exist "C:\IsoLens\artifacts\procmon" mkdir "C:\IsoLens\artifacts\procmon"
start "IsoLens Agent" cmd /c "cd /d C:\IsoLens\agent && python isolens_agent.py --host 0.0.0.0 --port 9090 --share Z:\ --workdir C:\IsoLens"

REM Give it 3 seconds to bind
timeout /t 3 /nobreak >NUL

REM Quick check
echo.
echo ========================================
echo   Verification
echo ========================================
netstat -an | findstr ":9090"
netstat -an | findstr ":22"
echo.
echo If you see LISTENING on ports 22 and 9090, setup is complete!
echo.
echo Test from host:
echo   curl http://192.168.56.105:9090/api/status
echo.
pause
