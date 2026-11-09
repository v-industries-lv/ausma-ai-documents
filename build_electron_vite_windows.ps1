# Ensure administrator privileges

$IsAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $IsAdmin) {
    $consent = Read-Host 'Build on windows requires administrator priviledges. Do you agree to proceed with elevated priviledges? Y/n'
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

# Run frontend setup in its own directory
Push-Location (Join-Path $PSScriptRoot 'frontend')
try {
    & .\build.ps1
}
finally {
    Pop-Location
}

# Run pyinstaller backend folder
Push-Location (Join-Path $PSScriptRoot 'backend')
try {
    & .\build_bundled.ps1
}
finally {
    Pop-Location
}

# Ensure pdftopng
$url = "https://dl.xpdfreader.com/xpdf-tools-win-4.06.zip"
$archive_file = "$env:TEMP\xpdf.zip"
$destination = Join-Path $PSScriptRoot "backend\bin\windows\pdftopng.exe"

$subfolder = if ([Environment]::Is64BitOperatingSystem) {
    "bin64"
} else {
    "bin32"
}

$entry = "xpdf-tools-win-4.06/$subfolder/pdftopng.exe"

Write-Output "Downloading xpdf tools from $url"
Invoke-WebRequest -Uri $url -OutFile $archive_file

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($archive_file)

try {
    $file = $archive.GetEntry($entry)

    if ($file) {
        $parent = Split-Path $destination -Parent
        New-Item -ItemType Directory -Path $parent -Force | Out-Null

        [System.IO.Compression.ZipFileExtensions]::ExtractToFile(
            $file, $destination, $true
        )

        Write-Output "Extracted to $destination"
    } else {
        throw "File not found in archive: $entry"
    }
}
finally {
    $archive.Dispose()
}


# Build app
Push-Location (Join-Path $PSScriptRoot 'electron-vite')
try {
    & .\build.ps1
}
finally {
    Pop-Location
}

Read-Host "Press Enter to exit"