# =============================================================================
# IsoLens VM Tool Installer
# =============================================================================
# Automated setup script for the IsoLens sandbox Windows VM.
# Run this ONCE inside the guest VM after a clean Windows install,
# before taking the baseline snapshot.
#
# USAGE (run as Administrator in PowerShell):
#   Set-ExecutionPolicy Bypass -Scope Process -Force
#   .\setup_vm_tools.ps1
#
# WHAT IT INSTALLS:
#   C:\Tools\
#     Sysmon64.exe          + sysmon_config.xml   (runs as Windows service)
#     Procmon64.exe
#     tshark.exe            (via Wireshark silent install)
#     fakenet\              (FakeNet-NG + Python deps)
#     screenshot_loop.ps1   (periodic screenshot helper)
#     isolens_agent.py      (the IsoLens guest agent — copied from SandboxShare)
#
# NOTES:
#   - Windows 7 SP1 64-bit compatible
#   - Wireshark 3.4.x is the last version supporting Windows 7
#   - FakeNet-NG requires Python 3 (bundled via embedded distribution)
#   - After this script completes, reboot and take a clean VM snapshot
# =============================================================================

#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

# ─── Configuration ─────────────────────────────────────────────────────────

$TOOLS_DIR        = "C:\Tools"
$ISOLENS_DIR      = "C:\IsoLens"
$SANDBOX_SHARE    = "\\VBOXSVR\SandboxShare"
$SYSMON_CONFIG    = "$TOOLS_DIR\sysmon_config.xml"
$PYTHON_EMBED_DIR = "$TOOLS_DIR\python"
$PYTHON_EXE       = "$PYTHON_EMBED_DIR\python.exe"
$AGENT_SRC        = "$SANDBOX_SHARE\isolens_agent.py"
$AGENT_DST        = "$TOOLS_DIR\isolens_agent.py"

# Download URLs
$URL_SYSMON       = "https://download.sysinternals.com/files/Sysmon.zip"
$URL_PROCMON      = "https://download.sysinternals.com/files/ProcessMonitor.zip"
# Wireshark 3.4.16 — last release supporting Windows 7
$URL_WIRESHARK    = "https://2.na.dl.wireshark.org/win64/Wireshark-win64-3.4.16.exe"
$URL_FAKENET      = "https://github.com/mandiant/flare-fakenet-ng/archive/refs/heads/master.zip"
# Python 3.8 embedded — last CPython supporting Windows 7
$URL_PYTHON_EMBED = "https://www.python.org/ftp/python/3.8.20/python-3.8.20-embed-amd64.zip"
$URL_PIP          = "https://bootstrap.pypa.io/pip/3.8/get-pip.py"

# ─── Helpers ───────────────────────────────────────────────────────────────

function Log($msg) {
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] $msg" -ForegroundColor Cyan
}

function LogOk($msg) {
    Write-Host "  ✔ $msg" -ForegroundColor Green
}

function LogWarn($msg) {
    Write-Host "  ⚠ $msg" -ForegroundColor Yellow
}

function LogErr($msg) {
    Write-Host "  ✘ $msg" -ForegroundColor Red
}

function Download($url, $dest) {
    Log "Downloading $(Split-Path $url -Leaf) ..."
    $wc = New-Object System.Net.WebClient
    $wc.DownloadFile($url, $dest)
    LogOk "Saved to $dest"
}

function Unzip($archive, $destDir) {
    Log "Extracting $archive → $destDir"
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($archive, $destDir)
    LogOk "Extracted"
}

function EnsureDir($path) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}

# ─── 0. Prepare directories ────────────────────────────────────────────────

Log "=== IsoLens VM Tool Installer ==="
Log "Tools directory: $TOOLS_DIR"

EnsureDir $TOOLS_DIR
EnsureDir $ISOLENS_DIR
EnsureDir "$ISOLENS_DIR\artifacts"
EnsureDir "$ISOLENS_DIR\samples"
EnsureDir "$TOOLS_DIR\downloads"

# ─── 1. Sysmon ─────────────────────────────────────────────────────────────

Log "--- [1/6] Sysmon ---"

$sysmon_zip = "$TOOLS_DIR\downloads\Sysmon.zip"
$sysmon_tmp = "$TOOLS_DIR\downloads\Sysmon"
EnsureDir $sysmon_tmp

Download $URL_SYSMON $sysmon_zip
Unzip $sysmon_zip $sysmon_tmp

# Copy exe to Tools root
$sysmon_src = if (Test-Path "$sysmon_tmp\Sysmon64.exe") { "$sysmon_tmp\Sysmon64.exe" } else { "$sysmon_tmp\Sysmon.exe" }
Copy-Item $sysmon_src "$TOOLS_DIR\Sysmon64.exe" -Force

# Write a minimal but effective Sysmon config targeting malware behaviour
# Based on core events only — process create, network, file create, registry
@'
<Sysmon schemaversion="4.90">
  <EventFiltering>

    <!-- Event ID 1: Process Creation — log everything -->
    <RuleGroup name="" groupRelation="or">
      <ProcessCreate onmatch="exclude"/>
    </RuleGroup>

    <!-- Event ID 2: File creation time changed -->
    <RuleGroup name="" groupRelation="or">
      <FileCreateTime onmatch="exclude"/>
    </RuleGroup>

    <!-- Event ID 3: Network connections — exclude common noise -->
    <RuleGroup name="" groupRelation="or">
      <NetworkConnect onmatch="exclude">
        <Image condition="is">C:\Windows\System32\svchost.exe</Image>
        <Image condition="is">C:\Windows\System32\lsass.exe</Image>
        <DestinationPort condition="is">443</DestinationPort>
      </NetworkConnect>
    </RuleGroup>

    <!-- Event ID 5: Process terminated -->
    <RuleGroup name="" groupRelation="or">
      <ProcessTerminate onmatch="exclude"/>
    </RuleGroup>

    <!-- Event ID 7: Image loaded (DLL loads) — exclude Microsoft signed -->
    <RuleGroup name="" groupRelation="or">
      <ImageLoad onmatch="exclude">
        <Signed condition="is">true</Signed>
      </ImageLoad>
    </RuleGroup>

    <!-- Event ID 8: CreateRemoteThread — catch injection attempts -->
    <RuleGroup name="" groupRelation="or">
      <CreateRemoteThread onmatch="exclude"/>
    </RuleGroup>

    <!-- Event ID 10: ProcessAccess — catch credential dumping -->
    <RuleGroup name="" groupRelation="or">
      <ProcessAccess onmatch="include">
        <TargetImage condition="end with">lsass.exe</TargetImage>
      </ProcessAccess>
    </RuleGroup>

    <!-- Event ID 11: FileCreate -->
    <RuleGroup name="" groupRelation="or">
      <FileCreate onmatch="exclude">
        <TargetFilename condition="begin with">C:\Windows\Prefetch</TargetFilename>
      </FileCreate>
    </RuleGroup>

    <!-- Event ID 12/13: Registry modifications — exclude system noise -->
    <RuleGroup name="" groupRelation="or">
      <RegistryEvent onmatch="exclude">
        <EventType condition="is not">SetValue</EventType>
      </RegistryEvent>
    </RuleGroup>

    <!-- Event ID 22: DNS queries -->
    <RuleGroup name="" groupRelation="or">
      <DnsQuery onmatch="exclude"/>
    </RuleGroup>

    <!-- Event ID 23: FileDelete -->
    <RuleGroup name="" groupRelation="or">
      <FileDelete onmatch="exclude"/>
    </RuleGroup>

  </EventFiltering>
</Sysmon>
'@ | Out-File -FilePath $SYSMON_CONFIG -Encoding UTF8

# Install Sysmon service (uninstall first if already present)
$svcExists = Get-Service "Sysmon64" -ErrorAction SilentlyContinue
if ($svcExists) {
    Log "Sysmon already installed — reinstalling with new config..."
    & "$TOOLS_DIR\Sysmon64.exe" -u 2>$null
    Start-Sleep -Seconds 2
}

Log "Installing Sysmon service..."
& "$TOOLS_DIR\Sysmon64.exe" -accepteula -i $SYSMON_CONFIG
if ($LASTEXITCODE -eq 0) {
    LogOk "Sysmon installed and running as a service"
} else {
    LogErr "Sysmon install may have had issues (exit code $LASTEXITCODE)"
}

# ─── 2. Procmon ────────────────────────────────────────────────────────────

Log "--- [2/6] Procmon ---"

$procmon_zip = "$TOOLS_DIR\downloads\ProcessMonitor.zip"
$procmon_tmp = "$TOOLS_DIR\downloads\ProcessMonitor"
EnsureDir $procmon_tmp

Download $URL_PROCMON $procmon_zip
Unzip $procmon_zip $procmon_tmp

$pmon_src = if (Test-Path "$procmon_tmp\Procmon64.exe") { "$procmon_tmp\Procmon64.exe" } else { "$procmon_tmp\Procmon.exe" }
Copy-Item $pmon_src "$TOOLS_DIR\Procmon64.exe" -Force
LogOk "Procmon64.exe → $TOOLS_DIR"

# ─── 3. Wireshark + tshark ─────────────────────────────────────────────────

Log "--- [3/6] Wireshark / tshark ---"

$ws_installer = "$TOOLS_DIR\downloads\Wireshark-win64.exe"
Download $URL_WIRESHARK $ws_installer

Log "Running Wireshark silent install (this may take a minute)..."
# /S = silent, /D sets install directory
Start-Process -FilePath $ws_installer `
    -ArgumentList "/S", "/D=C:\Wireshark" `
    -Wait -NoNewWindow

# Add tshark to PATH permanently
$tshark_path = "C:\Wireshark"
$current_path = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($current_path -notlike "*Wireshark*") {
    [Environment]::SetEnvironmentVariable(
        "PATH",
        "$current_path;$tshark_path",
        "Machine"
    )
    $env:PATH += ";$tshark_path"
    LogOk "tshark added to system PATH"
} else {
    LogOk "tshark already in PATH"
}

if (Test-Path "$tshark_path\tshark.exe") {
    LogOk "tshark.exe found at $tshark_path"
} else {
    LogWarn "tshark.exe not found — Wireshark may need manual install"
}

# ─── 4. Python (Embedded) + pip ────────────────────────────────────────────
#
# FakeNet-NG requires Python. We use the embedded distribution so it is
# fully self-contained inside C:\Tools and doesn't affect system Python.

Log "--- [4/6] Python (embedded) ---"

if (Test-Path $PYTHON_EXE) {
    LogOk "Python already present at $PYTHON_EXE — skipping download"
} else {
    $py_zip = "$TOOLS_DIR\downloads\python-embed.zip"
    EnsureDir $PYTHON_EMBED_DIR
    Download $URL_PYTHON_EMBED $py_zip
    Unzip $py_zip $PYTHON_EMBED_DIR

    # Enable site-packages so pip-installed packages are importable
    $pth_file = Get-ChildItem "$PYTHON_EMBED_DIR" -Filter "python38._pth" | Select-Object -First 1
    if ($pth_file) {
        (Get-Content $pth_file.FullName) -replace "#import site", "import site" |
            Set-Content $pth_file.FullName
    }

    # Install pip
    $get_pip = "$TOOLS_DIR\downloads\get-pip.py"
    Download $URL_PIP $get_pip
    & $PYTHON_EXE $get_pip --quiet
    LogOk "pip installed"
}

# Verify
$py_ver = & $PYTHON_EXE --version 2>&1
LogOk "Python: $py_ver"

# ─── 5. FakeNet-NG ─────────────────────────────────────────────────────────

Log "--- [5/6] FakeNet-NG ---"

$fakenet_zip = "$TOOLS_DIR\downloads\fakenet-ng.zip"
$fakenet_tmp = "$TOOLS_DIR\downloads\fakenet-ng-src"
$fakenet_dir = "$TOOLS_DIR\fakenet"

EnsureDir $fakenet_tmp
Download $URL_FAKENET $fakenet_zip
Unzip $fakenet_zip $fakenet_tmp

# Move extracted folder to C:\Tools\fakenet
$extracted = Get-ChildItem $fakenet_tmp -Directory | Select-Object -First 1
if ($extracted) {
    if (Test-Path $fakenet_dir) { Remove-Item $fakenet_dir -Recurse -Force }
    Move-Item $extracted.FullName $fakenet_dir
    LogOk "FakeNet-NG extracted → $fakenet_dir"
} else {
    LogErr "Could not find extracted FakeNet directory"
}

# Install FakeNet-NG Python dependencies
$fakenet_reqs = "$fakenet_dir\requirements.txt"
if (Test-Path $fakenet_reqs) {
    Log "Installing FakeNet-NG Python dependencies..."
    & $PYTHON_EXE -m pip install -r $fakenet_reqs --quiet
    LogOk "FakeNet-NG dependencies installed"
} else {
    LogWarn "requirements.txt not found in FakeNet dir — skipping pip install"
}

# ─── 6. Screenshot loop helper ─────────────────────────────────────────────

Log "--- [6/6] Screenshot helper ---"

# Writes a screenshot every N seconds to the screenshots artifact directory.
# The agent's ScreenshotCollector will pick these up at collection time.
@'
# IsoLens Screenshot Loop
# Usage: powershell -ExecutionPolicy Bypass -File screenshot_loop.ps1 [-Interval 5] [-OutDir "C:\IsoLens\artifacts\screenshots"]
param(
    [int]$Interval = 5,
    [string]$OutDir = "C:\IsoLens\artifacts\screenshots"
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

$idx = 0
Write-Host "[screenshot_loop] Started. Interval=${Interval}s  OutDir=$OutDir"
Write-Host "[screenshot_loop] Press Ctrl+C to stop."

while ($true) {
    $bounds  = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap  = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
    $graphic = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphic.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)

    $ts   = Get-Date -Format "yyyyMMdd_HHmmss"
    $file = Join-Path $OutDir "screenshot_${idx}_${ts}.png"
    $bitmap.Save($file, [System.Drawing.Imaging.ImageFormat]::Png)

    $graphic.Dispose()
    $bitmap.Dispose()

    $idx++
    Start-Sleep -Seconds $Interval
}
'@ | Out-File -FilePath "$TOOLS_DIR\screenshot_loop.ps1" -Encoding UTF8

LogOk "screenshot_loop.ps1 → $TOOLS_DIR"

# ─── 7. Copy IsoLens agent from shared folder ──────────────────────────────

Log "--- [7] IsoLens Agent ---"

if (Test-Path $AGENT_SRC) {
    Copy-Item $AGENT_SRC $AGENT_DST -Force
    LogOk "Agent copied: $AGENT_SRC → $AGENT_DST"
} else {
    LogWarn "Agent not found in SandboxShare ($AGENT_SRC)"
    LogWarn "Copy isolens_agent.py to SandboxShare and then copy manually to $TOOLS_DIR"
}

# ─── 8. Add Tools to PATH ──────────────────────────────────────────────────

$current_path = [Environment]::GetEnvironmentVariable("PATH", "Machine")
foreach ($p in @($TOOLS_DIR, $PYTHON_EMBED_DIR, "$PYTHON_EMBED_DIR\Scripts")) {
    if ($current_path -notlike "*$p*") {
        $current_path = "$current_path;$p"
    }
}
[Environment]::SetEnvironmentVariable("PATH", $current_path, "Machine")
$env:PATH = $current_path
LogOk "PATH updated with Tools, Python, and pip scripts directories"

# ─── Summary ───────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  IsoLens VM Setup Complete" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Installed:" -ForegroundColor White
Write-Host "    Sysmon64     → $TOOLS_DIR\Sysmon64.exe  (service running)" -ForegroundColor Gray
Write-Host "    Procmon64    → $TOOLS_DIR\Procmon64.exe" -ForegroundColor Gray
Write-Host "    tshark       → C:\Wireshark\tshark.exe" -ForegroundColor Gray
Write-Host "    FakeNet-NG   → $TOOLS_DIR\fakenet\" -ForegroundColor Gray
Write-Host "    Python 3.8   → $PYTHON_EXE" -ForegroundColor Gray
Write-Host "    Agent        → $TOOLS_DIR\isolens_agent.py" -ForegroundColor Gray
Write-Host "    Screenshots  → $TOOLS_DIR\screenshot_loop.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "    1. Reboot the VM" -ForegroundColor Gray
Write-Host "    2. Verify: sysmon64 -s  (show Sysmon config)" -ForegroundColor Gray
Write-Host "    3. Verify: tshark --version" -ForegroundColor Gray
Write-Host "    4. Take a clean VirtualBox snapshot (e.g. 'Baseline')" -ForegroundColor Gray
Write-Host ""
Write-Host "  To start the agent:" -ForegroundColor White
Write-Host "    python C:\Tools\isolens_agent.py --share \\VBOXSVR\SandboxShare" -ForegroundColor Gray
Write-Host ""
