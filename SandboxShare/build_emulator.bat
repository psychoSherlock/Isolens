@echo off
echo ============================================
echo  IsoLens Malware Emulator — Build Script
echo ============================================
echo.

:: Find the latest csc.exe from .NET Framework
set CSC=
for /f "delims=" %%i in ('dir /s /b %WINDIR%\Microsoft.NET\Framework64\v*\csc.exe 2^>nul') do set CSC=%%i
if "%CSC%"=="" (
    for /f "delims=" %%i in ('dir /s /b %WINDIR%\Microsoft.NET\Framework\v*\csc.exe 2^>nul') do set CSC=%%i
)
if "%CSC%"=="" (
    echo [ERROR] Could not find csc.exe. Is .NET Framework installed?
    pause
    exit /b 1
)

echo [*] Using compiler: %CSC%
echo [*] Compiling malware_emulator.cs ...
echo.

%CSC% /nologo /optimize /out:"%~dp0malware_emulator.exe" "%~dp0malware_emulator.cs"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Compilation failed.
    pause
    exit /b 1
)

echo.
echo [OK] Built: %~dp0malware_emulator.exe
echo.
echo You can now double-click malware_emulator.exe to run it.
echo.
pause
