# =======================================================================
#  IsoLens Windows 10 Setup Script
#  ---------------------------------------------------------------------
#  Run as Administrator (elevated PowerShell). Does everything:
#    1. Install and configure OpenSSH Server (built-in Windows 10 feature)
#    2. Deploy SSH public key for passwordless key-based login
#    3. Fix all SSH file/folder permissions (admin users need special ACL)
#    4. Configure auto-login without password prompt
#    5. Grant admin user full SSH access
#
#  Usage (from elevated PowerShell):
#    Set-ExecutionPolicy Bypass -Scope Process -Force
#    & Z:\setup_win10.ps1
# =======================================================================

param(
    [string]$Username = "admin",
    [string]$Password = "admin@2005"
)

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

# -- Check elevation ---------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Err "This script must be run as Administrator."
    Err "Right-click PowerShell -> Run as Administrator, then re-run."
    exit 1
}

# =======================================================================
#  STEP 1 -- Verify sshd is installed (via fix_sshd.ps1)
# =======================================================================
Banner "STEP 1: Verify OpenSSH Server"

# Check for the GitHub Win32-OpenSSH install (from fix_sshd.ps1)
$githubSshd = "C:\Program Files\OpenSSH\sshd.exe"
# Check for built-in System32 install
$builtinSshd = "$env:SystemRoot\System32\OpenSSH\sshd.exe"

$sshdPath = $null
if (Test-Path $githubSshd) {
    $sshdPath = $githubSshd
    Ok "Found Win32-OpenSSH at $githubSshd"
} elseif (Test-Path $builtinSshd) {
    $sshdPath = $builtinSshd
    Warn "Using built-in sshd at $builtinSshd"
    Warn "If sshd fails to start, run Z:\fix_sshd.ps1 first!"
} else {
    Err "sshd.exe not found anywhere!"
    Err "Run Z:\fix_sshd.ps1 first to install OpenSSH Server."
    exit 1
}

$sshdSvc = Get-Service sshd -ErrorAction SilentlyContinue
if (-not $sshdSvc) {
    Err "sshd service not registered."
    Err "Run Z:\fix_sshd.ps1 first to install OpenSSH Server."
    exit 1
}

$sshdInfo = Get-Item $sshdPath
Info "sshd.exe: $($sshdInfo.Length) bytes, date: $($sshdInfo.LastWriteTime)"
Ok "sshd service is registered."

# =======================================================================
#  STEP 2 -- Configure sshd_config
# =======================================================================
Banner "STEP 2: Configure sshd"

$sshDataDir     = "$env:ProgramData\ssh"
$sshdConfigPath = "$sshDataDir\sshd_config"

if (-not (Test-Path $sshdConfigPath)) {
    Err "sshd_config not found at $sshdConfigPath"
    Err "Run Z:\fix_sshd.ps1 first."
    exit 1
}

Info "Configuring $sshdConfigPath ..."
$config = Get-Content $sshdConfigPath

$config = $config -replace "^#?PubkeyAuthentication.*",   "PubkeyAuthentication yes"
$config = $config -replace "^#?PasswordAuthentication.*", "PasswordAuthentication yes"
$config = $config -replace "^#?PermitRootLogin.*",        "PermitRootLogin yes"
$config = $config -replace "^#?StrictModes.*",            "StrictModes no"
$config = $config -replace "^#?AuthorizedKeysFile.*",     "AuthorizedKeysFile .ssh/authorized_keys"

# CRITICAL: Comment out the admin Match block that overrides authorized_keys
$config = $config -replace "^Match Group administrators", "# Match Group administrators"
$config = $config -replace "^\s*AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys", "#       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys"

$config | Set-Content $sshdConfigPath -Force
Ok "sshd_config updated."

# Restart sshd to pick up config changes
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service ssh-agent -ErrorAction SilentlyContinue

if ((Get-Service sshd).Status -eq "Running") {
    Restart-Service sshd
    Info "sshd restarted with new config."
} else {
    Start-Service sshd
    Info "sshd started."
}
Ok "sshd is running."

# =======================================================================
#  STEP 3 -- Firewall Rule for SSH (Port 22)
# =======================================================================
Banner "STEP 3: Firewall Rule"

$rule = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue
if ($rule) {
    Ok "Firewall rule already exists."
} else {
    New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" `
        -DisplayName "OpenSSH Server (sshd)" `
        -Enabled True `
        -Direction Inbound `
        -Protocol TCP `
        -Action Allow `
        -LocalPort 22
    Ok "Firewall rule created for port 22."
}

# =======================================================================
#  STEP 4 -- Deploy SSH Public Key (key-based login)
# =======================================================================
Banner "STEP 4: Deploy SSH Public Key"

$publicKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEeQwhImS/8Wwkdmj655qb0Js9xjy+yBVMuTHoxmm4Bb isolens-sandbox"

# -- 4a: User-level authorized_keys --
$userHome = "C:\Users\$Username"
$sshDir   = Join-Path $userHome ".ssh"
$authKeys = Join-Path $sshDir "authorized_keys"

if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    Info "Created $sshDir"
}

if (Test-Path $authKeys) {
    $existing = Get-Content $authKeys -Raw
    if ($existing -notlike "*isolens-sandbox*") {
        Add-Content -Path $authKeys -Value $publicKey
        Info "Appended key to existing $authKeys"
    } else {
        Info "Key already present in $authKeys"
    }
} else {
    Set-Content -Path $authKeys -Value $publicKey -Encoding UTF8
    Info "Created $authKeys with IsoLens key."
}

# -- 4b: Also write to administrators_authorized_keys (fallback) --
$adminAuthKeys = "$env:ProgramData\ssh\administrators_authorized_keys"
if (-not (Test-Path $adminAuthKeys)) {
    Set-Content -Path $adminAuthKeys -Value $publicKey -Encoding UTF8
    Info "Created $adminAuthKeys"
} else {
    $existing2 = Get-Content $adminAuthKeys -Raw
    if ($existing2 -notlike "*isolens-sandbox*") {
        Add-Content -Path $adminAuthKeys -Value $publicKey
        Info "Appended key to $adminAuthKeys"
    } else {
        Info "Key already present in $adminAuthKeys"
    }
}

Ok "Public key deployed."

# =======================================================================
#  STEP 5 -- Fix SSH File Permissions (the critical part)
# =======================================================================
Banner "STEP 5: Fix SSH Permissions"

function Set-SshAcl {
    param(
        [string]$Path,
        [switch]$IncludeUser
    )

    if (-not (Test-Path $Path)) { return }

    $acl = Get-Acl $Path
    $acl.SetAccessRuleProtection($true, $false)

    # Remove all existing rules - copy to array first to avoid modifying during iteration
    $rules = @($acl.Access)
    foreach ($r in $rules) {
        $acl.RemoveAccessRule($r) | Out-Null
    }

    $fullControl = [System.Security.AccessControl.FileSystemRights]::FullControl
    $allow       = [System.Security.AccessControl.AccessControlType]::Allow

    # SYSTEM -- full control
    $systemSid  = New-Object System.Security.Principal.SecurityIdentifier("S-1-5-18")
    $systemRule = New-Object System.Security.AccessControl.FileSystemAccessRule($systemSid, $fullControl, $allow)
    $acl.AddAccessRule($systemRule)

    # Administrators -- full control
    $adminSid  = New-Object System.Security.Principal.SecurityIdentifier("S-1-5-32-544")
    $adminRule = New-Object System.Security.AccessControl.FileSystemAccessRule($adminSid, $fullControl, $allow)
    $acl.AddAccessRule($adminRule)

    # Optionally add the specific user
    if ($IncludeUser) {
        $userAccount = New-Object System.Security.Principal.NTAccount($Username)
        $userRule    = New-Object System.Security.AccessControl.FileSystemAccessRule($userAccount, $fullControl, $allow)
        $acl.AddAccessRule($userRule)
    }

    Set-Acl $Path $acl
    Info "Permissions fixed: $Path"
}

Set-SshAcl -Path $sshDir -IncludeUser
Set-SshAcl -Path $authKeys -IncludeUser
Set-SshAcl -Path $adminAuthKeys
Set-SshAcl -Path "$env:ProgramData\ssh"
Set-SshAcl -Path $sshdConfigPath

Ok "All SSH permissions fixed."

Restart-Service sshd
Ok "sshd restarted."

# =======================================================================
#  STEP 6 -- Configure Auto-Login (no password prompt at boot)
# =======================================================================
Banner "STEP 6: Configure Auto-Login"

$regPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"

Set-ItemProperty -Path $regPath -Name "AutoAdminLogon"  -Value "1"
Set-ItemProperty -Path $regPath -Name "DefaultUserName" -Value $Username
Set-ItemProperty -Path $regPath -Name "DefaultPassword" -Value $Password
Set-ItemProperty -Path $regPath -Name "ForceAutoLogon"  -Value "1"

Ok "Auto-login configured for '$Username'."
Info "Windows will boot straight to desktop without password prompt."

# =======================================================================
#  STEP 7 -- Create IsoLens directory structure
# =======================================================================
Banner "STEP 7: Create IsoLens Directories"

$dirs = @(
    "C:\IsoLens",
    "C:\IsoLens\tools",
    "C:\IsoLens\agent",
    "C:\IsoLens\artifacts"
)
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        Info "Created $d"
    }
}
Ok "IsoLens directory structure ready."

# =======================================================================
#  DONE
# =======================================================================
Banner "SETUP COMPLETE"

Write-Host ""
Ok "OpenSSH Server    : running (port 22, auto-start)"
Ok "Key-based login   : configured (isolens_vm_key)"
Ok "Password login    : also enabled (fallback)"
Ok "Auto-login        : $Username will auto-login at boot"
Ok "IsoLens dirs      : C:\IsoLens\{tools,agent,artifacts}"
Write-Host ""
Info "From your Linux host, connect with:"
Write-Host ""
Write-Host "    ssh -i ~/.ssh/isolens_vm_key admin@<vm-ip>" -ForegroundColor Yellow
Write-Host ""
Info "Reboot recommended to verify auto-login works."
Write-Host ""
