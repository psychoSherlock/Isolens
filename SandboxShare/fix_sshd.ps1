# =======================================================================
#  IsoLens -- Fix OpenSSH Server (replace broken built-in with GitHub release)
# =======================================================================
#  The Windows 10 built-in sshd.exe (2019) is incompatible with the
#  newer ssh-keygen (2025). This script downloads a matching release
#  from the official Win32-OpenSSH GitHub repo and installs it properly.
#
#  Run as Administrator:
#    Set-ExecutionPolicy Bypass -Scope Process -Force; & Z:\fix_sshd.ps1
# =======================================================================

$ErrorActionPreference = "Stop"

function Banner($msg) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}
function Info($msg)  { Write-Host "[*] $msg" -ForegroundColor White }
function Ok($msg)    { Write-Host "[+] $msg" -ForegroundColor Green }
function Warn($msg)  { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Err($msg)   { Write-Host "[X] $msg" -ForegroundColor Red }

# -- Check elevation --
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Err "Must run as Administrator."; exit 1
}

# =======================================================================
#  STEP 1 -- Stop existing sshd and remove broken capability
# =======================================================================
Banner "STEP 1: Remove broken built-in OpenSSH Server"

# Stop service if running
$sshdSvc = Get-Service sshd -ErrorAction SilentlyContinue
if ($sshdSvc -and $sshdSvc.Status -eq "Running") {
    Stop-Service sshd -Force
    Info "Stopped sshd service."
}

# Remove the Windows capability (this removes the old broken sshd.exe)
$cap = Get-WindowsCapability -Online | Where-Object Name -like "OpenSSH.Server*"
if ($cap -and $cap.State -eq "Installed") {
    Info "Removing OpenSSH.Server capability..."
    Remove-WindowsCapability -Online -Name "OpenSSH.Server~~~~0.0.1.0"
    Ok "Built-in OpenSSH Server removed."
} else {
    Info "OpenSSH.Server capability not installed (already removed or never present)."
}

# Also uninstall any existing Win32-OpenSSH service
$sshdExe = "$env:SystemRoot\System32\OpenSSH\sshd.exe"
if (Test-Path $sshdExe) {
    Info "Found leftover sshd.exe -- will be replaced."
}

# =======================================================================
#  STEP 2 -- Download Win32-OpenSSH from GitHub
# =======================================================================
Banner "STEP 2: Download Win32-OpenSSH"

$installDir = "C:\Program Files\OpenSSH"
$tempZip    = "$env:TEMP\OpenSSH-Win64.zip"
$tempExtract = "$env:TEMP\OpenSSH-Extract"

# Use the latest stable release URL
# v9.5.0.0p1-Beta is widely tested; we use the latest available
$downloadUrl = "https://github.com/PowerShell/Win32-OpenSSH/releases/latest/download/OpenSSH-Win64.zip"

Info "Downloading from: $downloadUrl"
Info "This may take a minute..."

# Use TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip -UseBasicParsing
    Ok "Downloaded OpenSSH-Win64.zip ($([math]::Round((Get-Item $tempZip).Length / 1MB, 1)) MB)"
} catch {
    Err "Download failed: $_"
    Err ""
    Err "Manual fallback: download OpenSSH-Win64.zip from"
    Err "  https://github.com/PowerShell/Win32-OpenSSH/releases"
    Err "and place it at: $tempZip"
    exit 1
}

# =======================================================================
#  STEP 3 -- Extract and install
# =======================================================================
Banner "STEP 3: Install OpenSSH"

# Clean up any previous extraction
if (Test-Path $tempExtract) { Remove-Item $tempExtract -Recurse -Force }

Info "Extracting..."
Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

# The zip contains a folder called OpenSSH-Win64
$extractedDir = Join-Path $tempExtract "OpenSSH-Win64"
if (-not (Test-Path $extractedDir)) {
    # Try finding whatever folder was extracted
    $extractedDir = Get-ChildItem $tempExtract -Directory | Select-Object -First 1 -ExpandProperty FullName
}

if (-not (Test-Path $extractedDir)) {
    Err "Could not find extracted OpenSSH folder."
    exit 1
}

# Remove old install dir if present
if (Test-Path $installDir) {
    Remove-Item $installDir -Recurse -Force
    Info "Removed old $installDir"
}

# Copy to final location
Copy-Item $extractedDir $installDir -Recurse -Force
Ok "Installed to $installDir"

# Show version
$newSshd = Join-Path $installDir "sshd.exe"
Info "sshd.exe size: $((Get-Item $newSshd).Length) bytes, date: $((Get-Item $newSshd).LastWriteTime)"

# =======================================================================
#  STEP 4 -- Add to PATH
# =======================================================================
Banner "STEP 4: Update PATH"

$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($machinePath -notlike "*$installDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$machinePath;$installDir", "Machine")
    Ok "Added $installDir to system PATH."
} else {
    Ok "$installDir already in PATH."
}

# Also update current session
$env:Path = "$env:Path;$installDir"

# =======================================================================
#  STEP 5 -- Generate host keys and configure
# =======================================================================
Banner "STEP 5: Generate Host Keys"

$sshDataDir = "$env:ProgramData\ssh"
if (-not (Test-Path $sshDataDir)) {
    New-Item -ItemType Directory -Path $sshDataDir -Force | Out-Null
}

# Generate host keys using the NEW matching ssh-keygen
$newKeygen = Join-Path $installDir "ssh-keygen.exe"
& $newKeygen -A
Ok "Host keys generated (matching sshd version)."

# List what was generated
Get-ChildItem "$sshDataDir\ssh_host_*" | ForEach-Object {
    Info "  $($_.Name) ($($_.Length) bytes)"
}

# =======================================================================
#  STEP 6 -- Create sshd_config
# =======================================================================
Banner "STEP 6: Configure sshd"

$sshdConfigPath = "$sshDataDir\sshd_config"

# Check for default config in the new install
$defaultConfig = Join-Path $installDir "sshd_config_default"
if (Test-Path $defaultConfig) {
    Copy-Item $defaultConfig $sshdConfigPath -Force
    Info "Copied default config from new install."
} else {
    # Write minimal config
    $minimalConfig = @"
Port 22
PubkeyAuthentication yes
PasswordAuthentication yes
PermitRootLogin yes
StrictModes no
AuthorizedKeysFile .ssh/authorized_keys
Subsystem sftp sftp-server.exe
"@
    Set-Content -Path $sshdConfigPath -Value $minimalConfig -Encoding ASCII
    Info "Wrote minimal sshd_config."
}

# Apply tweaks
$config = Get-Content $sshdConfigPath
$config = $config -replace "^#?PubkeyAuthentication.*",   "PubkeyAuthentication yes"
$config = $config -replace "^#?PasswordAuthentication.*", "PasswordAuthentication yes"
$config = $config -replace "^#?PermitRootLogin.*",        "PermitRootLogin yes"
$config = $config -replace "^#?StrictModes.*",            "StrictModes no"
$config = $config -replace "^#?AuthorizedKeysFile.*",     "AuthorizedKeysFile .ssh/authorized_keys"
$config = $config -replace "^Match Group administrators", "# Match Group administrators"
$config = $config -replace "^\s*AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys", "#       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys"
$config | Set-Content $sshdConfigPath -Force
Ok "sshd_config configured."

# =======================================================================
#  STEP 7 -- Install and start sshd as a Windows service
# =======================================================================
Banner "STEP 7: Install sshd Service"

# Run the install script that comes with Win32-OpenSSH
$installScript = Join-Path $installDir "install-sshd.ps1"
if (Test-Path $installScript) {
    Info "Running install-sshd.ps1..."
    & powershell.exe -ExecutionPolicy Bypass -File $installScript
    Ok "sshd service registered."
} else {
    # Manual service creation as fallback
    Info "install-sshd.ps1 not found -- creating service manually..."
    $sshdPath = Join-Path $installDir "sshd.exe"
    New-Service -Name sshd -BinaryPathName "`"$sshdPath`"" -DisplayName "OpenSSH SSH Server" -StartupType Automatic -Description "OpenSSH Server (Win32-OpenSSH)"
    Ok "sshd service created manually."
}

# Firewall rule
$rule = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue
if (-not $rule) {
    New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" `
        -DisplayName "OpenSSH Server (sshd)" `
        -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
    Ok "Firewall rule created."
} else {
    Ok "Firewall rule already exists."
}

# Start the service
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
$status = (Get-Service sshd).Status
if ($status -eq "Running") {
    Ok "sshd is RUNNING!"
} else {
    Err "sshd status: $status"
    Err "Trying debug mode for diagnostics..."
    & $newSshd -d -f $sshdConfigPath
}

# Also start ssh-agent
Set-Service -Name ssh-agent -StartupType Automatic -ErrorAction SilentlyContinue
Start-Service ssh-agent -ErrorAction SilentlyContinue

# =======================================================================
#  STEP 8 -- Verify
# =======================================================================
Banner "STEP 8: Verify"

$port22 = netstat -an | Select-String ":22 "
if ($port22) {
    Ok "Port 22 is listening:"
    $port22 | ForEach-Object { Info "  $_" }
} else {
    Err "Port 22 is NOT listening. Something is still wrong."
}

# Quick local test
Info "Testing local SSH connection..."
$testResult = & ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=3 localhost "echo SSH_OK" 2>&1
if ($testResult -like "*SSH_OK*") {
    Ok "Local SSH test PASSED!"
} else {
    Warn "Local SSH test -- could not auto-verify (may need password)."
    Warn "Try manually: ssh admin@localhost"
}

# =======================================================================
#  DONE
# =======================================================================
Banner "FIX COMPLETE"

Write-Host ""
Ok "OpenSSH Server installed from Win32-OpenSSH GitHub release"
Ok "sshd service: $((Get-Service sshd).Status)"
Ok "Install path: $installDir"
Write-Host ""
Info "From your Linux host:"
Write-Host "    ssh -i ~/.ssh/isolens_vm_key admin@<vm-ip>" -ForegroundColor Yellow
Write-Host ""
Info "Now run Z:\setup_win10.ps1 for the remaining setup (keys, autologin, etc)."
Write-Host ""

# Cleanup
Remove-Item $tempZip -Force -ErrorAction SilentlyContinue
Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue
