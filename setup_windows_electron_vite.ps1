# Ensure administrator privileges

$IsAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $IsAdmin) {
    $consent = Read-Host 'Setup on windows requires administrator priviledges to install. Do you agree to installing this application and its componenets with elevated priviledges? Y/n'
    if ($consent -and $consent -notmatch '^(y|yes)$') {
        Write-Host "Operation cancelled by user." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
    exit 0
}
    Start-Process powershell.exe `
        -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" `
        -WorkingDirectory $PSScriptRoot `
        -Verb RunAs
    exit
}

# Always work relative to the directory containing this script
Set-Location $PSScriptRoot

# Chocolatey install script

Set-ExecutionPolicy Bypass -Scope Process -Force

[System.Net.ServicePointManager]::SecurityProtocol = `
    [System.Net.ServicePointManager]::SecurityProtocol -bor 3072

iex ((New-Object System.Net.WebClient).DownloadString(
    'https://community.chocolatey.org/install.ps1'
))


# Run frontend setup in its own directory
Push-Location (Join-Path $PSScriptRoot 'frontend')
try {
    & .\setup_windows.ps1
}
finally {
    Pop-Location
}

# Run Python setup in its own directory
Push-Location (Join-Path $PSScriptRoot 'backend')
try {
    & .\setup_windows.ps1
}
finally {
    Pop-Location
}

Push-Location (Join-Path $PSScriptRoot 'electron-vite')
try {
    & .\setup_windows.ps1
}
finally {
    Pop-Location
}

Read-Host "Press Enter to exit"
