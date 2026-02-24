# fix_ssh_permissions.ps1
# Fixes ACLs for authorized_keys so OpenSSH accepts it

$sshDir = "$env:USERPROFILE\.ssh"
$authFile = "$sshDir\authorized_keys"

if (-not (Test-Path $authFile)) {
    Write-Host "[!] authorized_keys not found. Copy your key from Linux first."
    exit
}

Write-Host "[*] Fixing permissions on $authFile..."

# Disable inheritance and remove all inherited permissions
$acl = Get-Acl $authFile
$acl.SetAccessRuleProtection($true, $false)

# Grant full control only to the current user (admin) and SYSTEM
$user = New-Object System.Security.Principal.NTAccount($env:USERNAME)
$system = New-Object System.Security.Principal.NTAccount("SYSTEM")

$fullControl = [System.Security.AccessControl.FileSystemRights]::FullControl
$allow = [System.Security.AccessControl.AccessControlType]::Allow

$userRule = New-Object System.Security.AccessControl.FileSystemAccessRule($user, $fullControl, $allow)
$systemRule = New-Object System.Security.AccessControl.FileSystemAccessRule($system, $fullControl, $allow)

$acl.SetAccessRule($userRule)
$acl.AddAccessRule($systemRule)

Set-Acl $authFile $acl

Write-Host "[+] Permissions fixed. Passwordless login should now work."
