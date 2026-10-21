# run_vm_procmon.ps1 - Automated Procmon, Sysmon, and TCPVcon capture for malware_sim and legit_sim
$ErrorActionPreference = "Continue"

$toolsDir = "C:\IsoLens\tools"
$samplesDir = "C:\IsoLens\samples"
$artifactsDir = "C:\IsoLens\artifacts\test1"
$procmonExe = Join-Path $toolsDir "Procmon64.exe"
$tcpvconExe = Join-Path $toolsDir "tcpvcon64.exe"

if (-not (Test-Path $artifactsDir)) {
    New-Item -ItemType Directory -Path $artifactsDir -Force | Out-Null
}

function Run-VM-Test($exeName, $baseName) {
    Write-Host "=========================================================="
    Write-Host "[*] Starting test for $exeName..."
    Write-Host "=========================================================="

    $pmlFile = Join-Path $artifactsDir "$baseName.pml"
    $csvFile = Join-Path $artifactsDir "$baseName.csv"
    $sysmonXml = Join-Path $artifactsDir "$baseName`_sysmon.xml"
    $tcpvconCsv = Join-Path $artifactsDir "$baseName`_tcpvcon.csv"
    $targetExe = Join-Path $samplesDir $exeName

    # 1. Clean Sysmon logs for pristine baseline
    Write-Host "[*] Clearing Sysmon operational logs..."
    wevtutil cl Microsoft-Windows-Sysmon/Operational 2>$null
    Start-Sleep -Seconds 1

    # 2. Ensure Procmon is clean
    Start-Process -FilePath $procmonExe -ArgumentList "/Terminate" -Wait -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    # Remove old files if any
    if (Test-Path $pmlFile) { Remove-Item $pmlFile -Force }
    if (Test-Path $csvFile) { Remove-Item $csvFile -Force }
    if (Test-Path $sysmonXml) { Remove-Item $sysmonXml -Force }
    if (Test-Path $tcpvconCsv) { Remove-Item $tcpvconCsv -Force }

    # 3. Launch Procmon in background
    Write-Host "[*] Launching Procmon capturing to $pmlFile..."
    $procmon = Start-Process -FilePath $procmonExe -ArgumentList "/AcceptEula", "/Quiet", "/Minimized", "/BackingFile", $pmlFile -PassThru
    Start-Sleep -Seconds 3

    # 4. Execute the sample
    Write-Host "[*] Executing $targetExe..."
    $sampleProc = Start-Process -FilePath $targetExe -PassThru -Wait
    Write-Host "[+] Process $exeName exited with code $($sampleProc.ExitCode)"
    Start-Sleep -Seconds 2

    # 5. Capture TCPVcon snapshot
    if (Test-Path $tcpvconExe) {
        Write-Host "[*] Capturing TCPVcon connection table..."
        & $tcpvconExe -accepteula -a -c | Out-File -FilePath $tcpvconCsv -Encoding utf8
        Write-Host "[+] Exported TCPVcon snapshot to $tcpvconCsv"
    }

    # 6. Terminate Procmon to flush backing file
    Write-Host "[*] Terminating Procmon to flush data..."
    Start-Process -FilePath $procmonExe -ArgumentList "/Terminate" -Wait
    Start-Sleep -Seconds 3

    # Force kill if still lingering
    Get-Process -Name "procmon64", "procmon" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    # 7. Convert PML to CSV
    Write-Host "[*] Converting PML to CSV: $csvFile..."
    $convertProc = Start-Process -FilePath $procmonExe -ArgumentList "/OpenLog", $pmlFile, "/SaveAs", $csvFile, "/AcceptEula", "/Quiet" -PassThru
    $convertProc.WaitForExit(60000)
    Start-Sleep -Seconds 3

    # Force kill converter
    Get-Process -Name "procmon64", "procmon" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

    if (Test-Path $csvFile) {
        $size = (Get-Item $csvFile).Length
        Write-Host "[+] SUCCESS: Generated $csvFile ($([math]::Round($size / 1MB, 2)) MB)"
    } else {
        Write-Host "[-] WARNING: CSV file $csvFile not generated!"
    }

    # 8. Export Sysmon XML log
    Write-Host "[*] Exporting Sysmon operational log to $sysmonXml..."
    wevtutil qe Microsoft-Windows-Sysmon/Operational /f:xml > $sysmonXml
    if (Test-Path $sysmonXml) {
        $xmlSize = (Get-Item $sysmonXml).Length
        Write-Host "[+] SUCCESS: Exported Sysmon log ($xmlSize bytes)"
    }
}

# Run both tests
Run-VM-Test "malware_sim.exe" "procmon_malware_sim"
Run-VM-Test "legit_sim.exe" "procmon_legit_sim"

Write-Host "=========================================================="
Write-Host "[+] All VM Telemetry captures finished."
Write-Host "=========================================================="
