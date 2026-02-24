# =============================================================================
# IsoLens VM Hardening & Readiness Check
# =============================================================================
# Comprehensive diagnostic script that verifies the sandbox VM is properly
# configured for malware analysis. Run inside the guest VM as Administrator.
#
# USAGE:
#   Set-ExecutionPolicy Bypass -Scope Process -Force
#   .\check_vm_status.ps1
#
# CHECKS:
#   [01] Admin privileges
#   [02] OS version & architecture
#   [03] Guest Additions installed
#   [04] Shared folder accessible
#   [05] Directory structure
#   [06] Sysmon — binary present
#   [07] Sysmon — service running
#   [08] Sysmon — config loaded
#   [09] Sysmon — event log active
#   [10] Procmon — binary present
#   [11] tshark — binary present & on PATH
#   [12] FakeNet-NG — installed
#   [13] Python — embedded distribution
#   [14] IsoLens Agent — present
#   [15] IsoLens Agent — can import
#   [16] Screenshot helper — present
#   [17] Windows Defender — disabled
#   [18] Windows Update — disabled
#   [19] Windows Firewall — status
#   [20] UAC — level check
#   [21] Network adapters — host-only present
#   [22] Network adapters — NAT present
#   [23] Automatic Sample Submission — disabled
#   [24] SmartScreen — disabled
#   [25] PATH — tools directories
#   [26] Disk space — sufficient free space
#   [27] Memory — sufficient RAM
#   [28] Snapshot — current snapshot exists
# =============================================================================

#Requires -RunAsAdministrator

# ─── Configuration ─────────────────────────────────────────────────────────

$TOOLS_DIR        = "C:\Tools"
$ISOLENS_DIR      = "C:\IsoLens"
$SANDBOX_SHARE    = "\\VBOXSVR\SandboxShare"
$SYSMON_CONFIG    = "$TOOLS_DIR\sysmon_config.xml"
$PYTHON_EXE       = "$TOOLS_DIR\python\python.exe"
$AGENT_PATH       = "$TOOLS_DIR\isolens_agent.py"
$SCREENSHOT_PATH  = "$TOOLS_DIR\screenshot_loop.ps1"

# Minimum requirements
$MIN_FREE_DISK_GB = 3
$MIN_RAM_MB       = 1536

# ─── Tracking ──────────────────────────────────────────────────────────────

$script:total   = 0
$script:passed  = 0
$script:failed  = 0
$script:warned  = 0
$script:results = @()

# ─── Helpers ───────────────────────────────────────────────────────────────

function Pass($id, $name, $detail) {
    $script:total++
    $script:passed++
    $msg = "[PASS] [$id] $name"
    if ($detail) { $msg += " — $detail" }
    Write-Host $msg -ForegroundColor Green
    $script:results += @{ id=$id; name=$name; status="PASS"; detail=$detail }
}

function Fail($id, $name, $detail) {
    $script:total++
    $script:failed++
    $msg = "[FAIL] [$id] $name"
    if ($detail) { $msg += " — $detail" }
    Write-Host $msg -ForegroundColor Red
    $script:results += @{ id=$id; name=$name; status="FAIL"; detail=$detail }
}

function Warn($id, $name, $detail) {
    $script:total++
    $script:warned++
    $msg = "[WARN] [$id] $name"
    if ($detail) { $msg += " — $detail" }
    Write-Host $msg -ForegroundColor Yellow
    $script:results += @{ id=$id; name=$name; status="WARN"; detail=$detail }
}

function Section($title) {
    Write-Host ""
    Write-Host "━━━ $title ━━━" -ForegroundColor Cyan
}

# ─── [01] Admin Privileges ─────────────────────────────────────────────────

Section "ENVIRONMENT"

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if ($isAdmin) {
    Pass "01" "Administrator privileges" "Running elevated"
} else {
    Fail "01" "Administrator privileges" "Script must run as Administrator"
}

# ─── [02] OS Version & Architecture ────────────────────────────────────────

$os = Get-WmiObject Win32_OperatingSystem
$osCaption = $os.Caption.Trim()
$osArch = $os.OSArchitecture

if ($osArch -like "*64*") {
    Pass "02" "OS version & architecture" "$osCaption ($osArch)"
} else {
    Warn "02" "OS version & architecture" "$osCaption ($osArch) — 64-bit recommended"
}

# ─── [03] VirtualBox Guest Additions ───────────────────────────────────────

$gaService = Get-Service "VBoxService" -ErrorAction SilentlyContinue
if ($gaService -and $gaService.Status -eq "Running") {
    Pass "03" "VirtualBox Guest Additions" "VBoxService running"
} elseif ($gaService) {
    Warn "03" "VirtualBox Guest Additions" "VBoxService exists but status: $($gaService.Status)"
} else {
    Fail "03" "VirtualBox Guest Additions" "VBoxService not found — install Guest Additions"
}

# ─── [04] Shared Folder ───────────────────────────────────────────────────

if (Test-Path $SANDBOX_SHARE) {
    $items = (Get-ChildItem $SANDBOX_SHARE -ErrorAction SilentlyContinue | Measure-Object).Count
    Pass "04" "Shared folder accessible" "$SANDBOX_SHARE ($items items)"
} else {
    Fail "04" "Shared folder accessible" "$SANDBOX_SHARE not found — check VirtualBox shared folder config"
}

# ─── [05] Directory Structure ──────────────────────────────────────────────

Section "DIRECTORY STRUCTURE"

$dirs_ok = $true
$dirs_detail = @()

foreach ($d in @($TOOLS_DIR, $ISOLENS_DIR, "$ISOLENS_DIR\artifacts", "$ISOLENS_DIR\samples")) {
    if (Test-Path $d) {
        $dirs_detail += "$d ✔"
    } else {
        $dirs_detail += "$d ✘"
        $dirs_ok = $false
    }
}

if ($dirs_ok) {
    Pass "05" "Directory structure" "All directories present"
} else {
    Fail "05" "Directory structure" "Missing: $($dirs_detail -join ', ')"
}

# ─── [06–09] Sysmon ───────────────────────────────────────────────────────

Section "SYSMON"

# 06: Binary
$sysmonExe = "$TOOLS_DIR\Sysmon64.exe"
if (Test-Path $sysmonExe) {
    Pass "06" "Sysmon binary present" $sysmonExe
} else {
    Fail "06" "Sysmon binary present" "Sysmon64.exe not found in $TOOLS_DIR"
}

# 07: Service
$sysmonSvc = Get-Service "Sysmon64" -ErrorAction SilentlyContinue
if (-not $sysmonSvc) {
    $sysmonSvc = Get-Service "Sysmon" -ErrorAction SilentlyContinue
}
if ($sysmonSvc -and $sysmonSvc.Status -eq "Running") {
    Pass "07" "Sysmon service running" "Service: $($sysmonSvc.Name) ($($sysmonSvc.Status))"
} elseif ($sysmonSvc) {
    Fail "07" "Sysmon service running" "Service exists but status: $($sysmonSvc.Status) — try: net start Sysmon64"
} else {
    Fail "07" "Sysmon service running" "No Sysmon service found — install with: Sysmon64.exe -i config.xml"
}

# 08: Config file
if (Test-Path $SYSMON_CONFIG) {
    $configSize = (Get-Item $SYSMON_CONFIG).Length
    Pass "08" "Sysmon config loaded" "$SYSMON_CONFIG ($configSize bytes)"
} else {
    Warn "08" "Sysmon config loaded" "Config file not at $SYSMON_CONFIG (Sysmon may use default config)"
}

# 09: Event log channel
try {
    $logCheck = wevtutil gl "Microsoft-Windows-Sysmon/Operational" 2>&1
    if ($LASTEXITCODE -eq 0) {
        # Check if the log is enabled
        $enabled = $logCheck | Select-String "enabled:\s*true" -Quiet
        if ($enabled) {
            Pass "09" "Sysmon event log active" "Microsoft-Windows-Sysmon/Operational is enabled"
        } else {
            Warn "09" "Sysmon event log active" "Channel exists but may not be enabled"
        }
    } else {
        Fail "09" "Sysmon event log active" "Channel not found — Sysmon not properly installed"
    }
} catch {
    Fail "09" "Sysmon event log active" "Could not query event log: $_"
}

# ─── [10] Procmon ──────────────────────────────────────────────────────────

Section "PROCMON"

$procmonPaths = @(
    "$TOOLS_DIR\Procmon64.exe",
    "$TOOLS_DIR\Procmon.exe",
    "C:\SysinternalsSuite\Procmon64.exe",
    "C:\SysinternalsSuite\Procmon.exe"
)
$procmonFound = $procmonPaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($procmonFound) {
    Pass "10" "Procmon binary present" $procmonFound
} else {
    Fail "10" "Procmon binary present" "Procmon not found in any expected path"
}

# ─── [11] tshark ───────────────────────────────────────────────────────────

Section "TSHARK / WIRESHARK"

$tsharkExe = Get-Command "tshark" -ErrorAction SilentlyContinue
if ($tsharkExe) {
    try {
        $ver = & tshark --version 2>&1 | Select-Object -First 1
        Pass "11" "tshark on PATH" "$($tsharkExe.Source) — $ver"
    } catch {
        Pass "11" "tshark on PATH" $tsharkExe.Source
    }
} elseif (Test-Path "C:\Wireshark\tshark.exe") {
    Warn "11" "tshark on PATH" "Found at C:\Wireshark\tshark.exe but NOT on PATH — add to PATH"
} else {
    Fail "11" "tshark on PATH" "tshark not found — install Wireshark"
}

# ─── [12] FakeNet-NG ──────────────────────────────────────────────────────

Section "FAKENET-NG"

$fakenetDir = "$TOOLS_DIR\fakenet"
$fakenetScript = "$fakenetDir\fakenet.py"

if (Test-Path $fakenetDir) {
    if (Test-Path $fakenetScript) {
        Pass "12" "FakeNet-NG installed" $fakenetDir
    } else {
        Warn "12" "FakeNet-NG installed" "Directory exists but fakenet.py not found"
    }
} else {
    Fail "12" "FakeNet-NG installed" "Not found at $fakenetDir"
}

# ─── [13] Python ──────────────────────────────────────────────────────────

Section "PYTHON"

if (Test-Path $PYTHON_EXE) {
    try {
        $pyVer = & $PYTHON_EXE --version 2>&1
        Pass "13" "Python embedded distribution" "$PYTHON_EXE — $pyVer"
    } catch {
        Warn "13" "Python embedded distribution" "Binary exists but could not get version"
    }
} else {
    # Check system python as fallback
    $sysPython = Get-Command "python" -ErrorAction SilentlyContinue
    if ($sysPython) {
        $pyVer = & python --version 2>&1
        Warn "13" "Python embedded distribution" "Not at $PYTHON_EXE, but system Python found: $pyVer"
    } else {
        Fail "13" "Python embedded distribution" "Python not found"
    }
}

# ─── [14–15] IsoLens Agent ────────────────────────────────────────────────

Section "ISOLENS AGENT"

# 14: File present
if (Test-Path $AGENT_PATH) {
    $agentSize = (Get-Item $AGENT_PATH).Length
    Pass "14" "Agent script present" "$AGENT_PATH ($agentSize bytes)"
} else {
    Fail "14" "Agent script present" "Not found at $AGENT_PATH"
}

# 15: Can import (syntax check)
if ((Test-Path $AGENT_PATH) -and (Test-Path $PYTHON_EXE)) {
    try {
        $syntaxCheck = & $PYTHON_EXE -c "import py_compile; py_compile.compile(r'$AGENT_PATH', doraise=True)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Pass "15" "Agent syntax valid" "Python can parse isolens_agent.py"
        } else {
            Fail "15" "Agent syntax valid" "Syntax errors: $syntaxCheck"
        }
    } catch {
        Fail "15" "Agent syntax valid" "Check failed: $_"
    }
} elseif (Test-Path $AGENT_PATH) {
    Warn "15" "Agent syntax valid" "Skipped — Python not available to verify"
} else {
    Fail "15" "Agent syntax valid" "Skipped — agent file missing"
}

# ─── [16] Screenshot Helper ──────────────────────────────────────────────

# 16: Script present
if (Test-Path $SCREENSHOT_PATH) {
    Pass "16" "Screenshot helper present" $SCREENSHOT_PATH
} else {
    Fail "16" "Screenshot helper present" "Not found at $SCREENSHOT_PATH"
}

# ─── [17–20] Windows Security Settings ───────────────────────────────────

Section "WINDOWS SECURITY (sandbox hardening)"

# 17: Windows Defender
try {
    $defenderStatus = Get-MpComputerStatus -ErrorAction SilentlyContinue
    if ($defenderStatus) {
        $rtEnabled = $defenderStatus.RealTimeProtectionEnabled
        if (-not $rtEnabled) {
            Pass "17" "Windows Defender real-time protection" "Disabled (good for sandbox)"
        } else {
            Fail "17" "Windows Defender real-time protection" "ENABLED — will quarantine malware samples. Disable via: Set-MpPreference -DisableRealtimeMonitoring `$true"
        }
    } else {
        Pass "17" "Windows Defender real-time protection" "Defender not present (Windows 7)"
    }
} catch {
    # Get-MpComputerStatus doesn't exist on Win7
    # Check via WMI for older AV products
    try {
        $av = Get-WmiObject -Namespace "root\SecurityCenter2" -Class "AntiVirusProduct" -ErrorAction SilentlyContinue
        if ($av) {
            Warn "17" "Antivirus detected" "Found: $($av.displayName) — ensure it won't block samples"
        } else {
            Pass "17" "Antivirus status" "No antivirus product detected (good for sandbox)"
        }
    } catch {
        Warn "17" "Antivirus status" "Could not determine AV status"
    }
}

# 18: Windows Update
try {
    $wuService = Get-Service "wuauserv" -ErrorAction SilentlyContinue
    if ($wuService) {
        $startType = $wuService.StartType
        if ($wuService.Status -eq "Stopped" -and $startType -eq "Disabled") {
            Pass "18" "Windows Update service" "Disabled (good for sandbox)"
        } elseif ($wuService.Status -eq "Stopped") {
            Warn "18" "Windows Update service" "Stopped but start type is '$startType' — set to Disabled: Set-Service wuauserv -StartupType Disabled"
        } else {
            Fail "18" "Windows Update service" "Status: $($wuService.Status), StartType: $startType — disable to prevent interference"
        }
    } else {
        Pass "18" "Windows Update service" "Service not found"
    }
} catch {
    Warn "18" "Windows Update service" "Could not check: $_"
}

# 19: Windows Firewall
try {
    $fwProfiles = netsh advfirewall show allprofiles state 2>&1
    $fwOn = ($fwProfiles | Select-String "ON" | Measure-Object).Count
    $fwOff = ($fwProfiles | Select-String "OFF" | Measure-Object).Count

    if ($fwOff -gt 0 -and $fwOn -eq 0) {
        Pass "19" "Windows Firewall" "All profiles OFF (sandbox mode)"
    } elseif ($fwOn -gt 0 -and $fwOff -gt 0) {
        Warn "19" "Windows Firewall" "$fwOn profile(s) ON, $fwOff OFF — consider disabling all for analysis"
    } elseif ($fwOn -gt 0) {
        Warn "19" "Windows Firewall" "All profiles ON — may block malware network activity. Disable with: netsh advfirewall set allprofiles state off"
    } else {
        Warn "19" "Windows Firewall" "Could not determine status"
    }
} catch {
    Warn "19" "Windows Firewall" "Could not check: $_"
}

# 20: UAC level
try {
    $uacKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
    $enableLUA = (Get-ItemProperty -Path $uacKey -Name "EnableLUA" -ErrorAction SilentlyContinue).EnableLUA
    $consentPrompt = (Get-ItemProperty -Path $uacKey -Name "ConsentPromptBehaviorAdmin" -ErrorAction SilentlyContinue).ConsentPromptBehaviorAdmin

    if ($enableLUA -eq 0) {
        Pass "20" "UAC disabled" "EnableLUA = 0 (fully disabled)"
    } elseif ($consentPrompt -eq 0) {
        Pass "20" "UAC level" "UAC enabled but no prompt for admins (ConsentPromptBehaviorAdmin = 0)"
    } else {
        Warn "20" "UAC level" "UAC active (EnableLUA=$enableLUA, ConsentPrompt=$consentPrompt) — may block silent execution"
    }
} catch {
    Warn "20" "UAC level" "Could not check: $_"
}

# ─── [21–22] Network Adapters ────────────────────────────────────────────

Section "NETWORK"

$adapters = Get-WmiObject Win32_NetworkAdapter | Where-Object { $_.NetEnabled -eq $true }

# 21: Host-only adapter
$hostOnly = $adapters | Where-Object {
    $_.Name -like "*Host-Only*" -or
    $_.Name -like "*VirtualBox Host*" -or
    $_.Description -like "*Host-Only*"
}
if ($hostOnly) {
    $hoName = ($hostOnly | Select-Object -First 1).Name
    Pass "21" "Host-only network adapter" $hoName
} else {
    Fail "21" "Host-only network adapter" "No host-only adapter found — agent needs this for host communication"
}

# 22: NAT adapter
$natAdapter = $adapters | Where-Object {
    $_.Name -notlike "*Host-Only*" -and
    $_.Name -notlike "*VirtualBox Host*" -and
    $_.Description -notlike "*Host-Only*"
}
if ($natAdapter) {
    $natName = ($natAdapter | Select-Object -First 1).Name
    Pass "22" "NAT/bridged network adapter" $natName
} else {
    Warn "22" "NAT/bridged network adapter" "No second adapter found — FakeNet can simulate internet, but some malware needs a real (NAT) adapter to trigger"
}

# ─── [23] Automatic Sample Submission ────────────────────────────────────

Section "PRIVACY & INTERFERENCE"

try {
    $spynet = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows Defender\Spynet" -Name "SubmitSamplesConsent" -ErrorAction SilentlyContinue).SubmitSamplesConsent
    if ($spynet -eq 0 -or $spynet -eq $null) {
        Pass "23" "Automatic sample submission" "Disabled or not configured"
    } else {
        Fail "23" "Automatic sample submission" "Enabled (value=$spynet) — malware samples may be uploaded to Microsoft"
    }
} catch {
    Pass "23" "Automatic sample submission" "Registry key not present (likely Windows 7)"
}

# 24: SmartScreen
try {
    $ssKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer"
    $ssValue = (Get-ItemProperty -Path $ssKey -Name "SmartScreenEnabled" -ErrorAction SilentlyContinue).SmartScreenEnabled
    if ($ssValue -eq "Off" -or $ssValue -eq $null) {
        Pass "24" "SmartScreen filter" "Disabled or not present"
    } else {
        Warn "24" "SmartScreen filter" "Value: $ssValue — may block downloaded executables"
    }
} catch {
    Pass "24" "SmartScreen filter" "Not present (likely Windows 7)"
}

# ─── [25] PATH ───────────────────────────────────────────────────────────

Section "SYSTEM PATH"

$sysPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
$pathChecks = @(
    @{ name="C:\Tools";          present=($sysPath -like "*C:\Tools*") },
    @{ name="C:\Tools\python";   present=($sysPath -like "*C:\Tools\python*") },
    @{ name="C:\Wireshark";      present=($sysPath -like "*Wireshark*") }
)

$allOnPath = $true
$pathDetail = @()
foreach ($pc in $pathChecks) {
    if ($pc.present) {
        $pathDetail += "$($pc.name) ✔"
    } else {
        $pathDetail += "$($pc.name) ✘"
        $allOnPath = $false
    }
}

if ($allOnPath) {
    Pass "25" "Tools directories on PATH" ($pathDetail -join ", ")
} else {
    Warn "25" "Tools directories on PATH" ($pathDetail -join ", ")
}

# ─── [26] Disk Space ────────────────────────────────────────────────────

Section "RESOURCES"

try {
    $disk = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
    $freeGB = [math]::Round($disk.FreeSpace / 1GB, 1)
    $totalGB = [math]::Round($disk.Size / 1GB, 1)

    if ($freeGB -ge $MIN_FREE_DISK_GB) {
        Pass "26" "Disk space" "${freeGB}GB free / ${totalGB}GB total"
    } else {
        Fail "26" "Disk space" "Only ${freeGB}GB free (need ${MIN_FREE_DISK_GB}GB+) / ${totalGB}GB total"
    }
} catch {
    Warn "26" "Disk space" "Could not check: $_"
}

# ─── [27] RAM ────────────────────────────────────────────────────────────

try {
    $totalRAM = [math]::Round($os.TotalVisibleMemorySize / 1024)
    $freeRAM  = [math]::Round($os.FreePhysicalMemory / 1024)

    if ($totalRAM -ge $MIN_RAM_MB) {
        Pass "27" "System memory" "${totalRAM}MB total, ${freeRAM}MB free"
    } else {
        Warn "27" "System memory" "${totalRAM}MB total (recommend ${MIN_RAM_MB}MB+), ${freeRAM}MB free"
    }
} catch {
    Warn "27" "System memory" "Could not check: $_"
}

# ─── [28] VirtualBox Snapshot ────────────────────────────────────────────

Section "SNAPSHOT"

# We can't directly query snapshots from inside the VM, but we can check
# if the VM was restored from a snapshot by looking for the VBox marker
try {
    $vboxGuestProps = & "C:\Program Files\Oracle\VirtualBox Guest Additions\VBoxControl.exe" guestproperty enumerate 2>&1
    if ($LASTEXITCODE -eq 0) {
        Pass "28" "VirtualBox guest properties" "VBoxControl accessible — host can manage snapshots"
    } else {
        Warn "28" "VirtualBox guest properties" "VBoxControl returned error"
    }
} catch {
    try {
        $vboxGuestProps2 = & "VBoxControl.exe" guestproperty enumerate 2>&1
        if ($LASTEXITCODE -eq 0) {
            Pass "28" "VirtualBox guest properties" "VBoxControl accessible"
        } else {
            Warn "28" "VirtualBox guest properties" "VBoxControl not functional"
        }
    } catch {
        Warn "28" "VirtualBox guest properties" "VBoxControl not found — ensure Guest Additions are installed"
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host "  IsoLens VM Readiness Report" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host ""

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "  Timestamp:  $ts"
Write-Host "  Machine:    $($os.CSName)"
Write-Host "  OS:         $osCaption"
Write-Host ""

Write-Host "  Total checks:  $($script:total)" -ForegroundColor White

if ($script:passed -gt 0) {
    Write-Host "  Passed:        $($script:passed)" -ForegroundColor Green
}
if ($script:warned -gt 0) {
    Write-Host "  Warnings:      $($script:warned)" -ForegroundColor Yellow
}
if ($script:failed -gt 0) {
    Write-Host "  Failed:        $($script:failed)" -ForegroundColor Red
}

Write-Host ""

if ($script:failed -eq 0 -and $script:warned -eq 0) {
    Write-Host "  ✔ VM is FULLY READY for malware analysis" -ForegroundColor Green
} elseif ($script:failed -eq 0) {
    Write-Host "  ⚠ VM is READY with minor warnings — review items above" -ForegroundColor Yellow
} else {
    Write-Host "  ✘ VM has FAILED checks — fix the issues above before taking a snapshot" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor White

# ─── Export results to SandboxShare (if accessible) ────────────────────────

try {
    if (Test-Path $SANDBOX_SHARE) {
        $reportName = "vm_status_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
        $reportPath = Join-Path $SANDBOX_SHARE $reportName

        $reportLines = @(
            "IsoLens VM Readiness Report"
            "Generated: $ts"
            "Machine:   $($os.CSName)"
            "OS:        $osCaption"
            ""
            "Results:"
            "─────────────────────────────────────────────────"
        )

        foreach ($r in $script:results) {
            $line = "[$($r.status)] [$($r.id)] $($r.name)"
            if ($r.detail) { $line += " — $($r.detail)" }
            $reportLines += $line
        }

        $reportLines += ""
        $reportLines += "─────────────────────────────────────────────────"
        $reportLines += "PASS: $($script:passed)  WARN: $($script:warned)  FAIL: $($script:failed)  TOTAL: $($script:total)"

        $reportLines | Out-File -FilePath $reportPath -Encoding UTF8
        Write-Host "  Report saved → $reportPath" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Could not save report to SandboxShare: $_" -ForegroundColor Gray
}

Write-Host ""
