# install_openssh.ps1 (Legacy Version for Windows 7 / PowerShell 2.0)
# Automates OpenSSH installation and configuration for IsoLens Sandbox

$zipPath = "Z:\OpenSSH-Win64.zip"
$installDir = "C:\Program Files\OpenSSH"

Write-Host "[*] Starting OpenSSH Setup (Legacy Mode)..."

# 1. Check if zip exists
if (-not (Test-Path $zipPath)) {
    Write-Host "[!] Error: OpenSSH zip not found at $zipPath"
    Write-Host "[i] Ensure the SandboxShare folder is mapped to Z: drive."
    exit 1
}

# 2. Extraction using Shell.Application (PowerShell 2.0 compatible)
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Force -Path $installDir
}

Write-Host "[*] Extracting $zipPath to $installDir..."
$tempExtract = "C:\Temp\OpenSSH_Extract"
if (Test-Path $tempExtract) { Remove-Item -Recurse -Force $tempExtract }
New-Item -ItemType Directory -Force -Path $tempExtract

$shell = New-Object -ComObject Shell.Application
$zipFile = $shell.NameSpace($zipPath)
$destFolder = $shell.NameSpace($tempExtract)
$destFolder.CopyHere($zipFile.Items(), 0x10)

# Find the inner folder (using PSIsContainer for PS 2.0 compatibility)
$innerFolder = Get-ChildItem -Path $tempExtract | Where-Object { $_.PSIsContainer } | Select-Object -First 1
$sourcePath = Join-Path $innerFolder.FullName "*"
Copy-Item -Path $sourcePath -Destination $installDir -Recurse -Force

# 3. Install Service
Write-Host "[*] Running install-sshd.ps1..."
Set-Location $installDir
& .\install-sshd.ps1

# 4. Configure Firewall (using netsh for Windows 7)
Write-Host "[*] Opening Firewall Port 22 via netsh..."
netsh advfirewall firewall delete rule name="OpenSSH Server (sshd)"
netsh advfirewall firewall add rule name="OpenSSH Server (sshd)" dir=in action=allow protocol=TCP localport=22

# 5. Allow Admin Login & Configure sshd_config
Write-Host "[*] Configuring sshd_config..."
$configPath = "$installDir\sshd_config"
if (Test-Path $configPath) {
    (Get-Content $configPath) | ForEach-Object {
        $_ -replace '^#?PasswordAuthentication.*', 'PasswordAuthentication yes' `
           -replace '^#?PermitRootLogin.*', 'PermitRootLogin yes' `
           -replace '^#?StrictModes.*', 'StrictModes no'
    } | Set-Content $configPath
}

# 6. Start Service (using sc.exe for startup type in PS 2.0)
Write-Host "[*] Starting OpenSSH services..."
sc.exe config sshd start= auto
Start-Service -Name sshd
sc.exe config ssh-agent start= auto
Start-Service -Name ssh-agent

Write-Host "[+] OpenSSH installation complete!"
