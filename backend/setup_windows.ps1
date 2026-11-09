# Get XPDF pdf to png convertor

$url = "https://dl.xpdfreader.com/xpdf-tools-win-4.06.zip"
$archive_file = "$env:TEMP\xpdf.zip"
$destination = "bin\windows\pdftopng.exe"

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

# Install ollama and pull default models

choco install ollama -y

$response = Read-Host 'Do you want to pull default ollama models (recommended)? Y/n'
if ($response -match '^(Y|Yes)$') {
    Write-Output "Pulling ollama models..."

    # Default LLMs for proofreading and transcribing
    ollama pull qwen2.5
    ollama pull qwen2.5vl

    # General-purpose multimodal LLMs
    ollama pull qwen3-vl:latest
    ollama pull gemma4:latest

    # Embedding model
    ollama pull bge-m3
}

# Install tesseract for basic ocr

choco install tesseract -y

& .\setup_python_windows.ps1

