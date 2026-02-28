# enable_autologin.ps1
# Configures Windows 7 to log in automatically at boot

$username = "admin"
$password = "admin@2005" # <--- CHANGE THIS

Write-Host "[*] Configuring Registry for Auto-Login..."

$regPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"

Set-ItemProperty -Path $regPath -Name "AutoAdminLogon" -Value "1"
Set-ItemProperty -Path $regPath -Name "DefaultUserName" -Value $username
Set-ItemProperty -Path $regPath -Name "DefaultPassword" -Value $password
Set-ItemProperty -Path $regPath -Name "ForceAutoLogon" -Value "1"

Write-Host "[+] Auto-login configured for $username."
Write-Host "[!] Note: Ensure you have set a password for the account first."
