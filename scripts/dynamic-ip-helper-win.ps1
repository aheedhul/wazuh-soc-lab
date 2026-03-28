# dynamic-ip-helper-win.ps1
# Updates the Wazuh Windows agent to point at a new manager IP.
# Must be run as Administrator (elevated PowerShell).
# Usage: .\dynamic-ip-helper-win.ps1

param(
    [string]$NewIP
)

Write-Host "--- Wazuh Windows Agent Dynamic IP Helper ---" -ForegroundColor Cyan

# Prompt for IP if not passed as argument
if (-not $NewIP) {
    $NewIP = Read-Host "Enter the new Ubuntu server (Wazuh manager) IP address"
}

# Validate IP format
if ($NewIP -notmatch '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$') {
    Write-Host "[!] Error: Invalid IP address format." -ForegroundColor Red
    exit 1
}

$configPath = "C:\Program Files (x86)\ossec-agent\ossec.conf"

# Verify we're running elevated
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if (-not $isAdmin) {
    Write-Host "[!] Error: Run this script as Administrator." -ForegroundColor Red
    exit 1
}

# Update the <address> tag in ossec.conf
Write-Host "[*] Updating configuration file..."
$content = Get-Content $configPath -Raw
$updated = $content -replace '<address>.*?</address>', "<address>$NewIP</address>"
Set-Content -Path $configPath -Value $updated -NoNewline

# Restart the Wazuh agent service
Write-Host "[*] Restarting Wazuh agent service..."
Restart-Service WazuhSvc

Write-Host "[+] Success! Windows agent is now reporting to $NewIP" -ForegroundColor Green
