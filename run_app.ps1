# Build frontend
Push-Location (Join-Path $PSScriptRoot 'frontend')
try {
    & .\build.ps1

    if ($LASTEXITCODE -ne 0) {
        throw "Frontend build failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

# Run backend, passing the frontend distribution path
Push-Location (Join-Path $PSScriptRoot 'backend')
try {
    & .\run_app.ps1 --frontend_path "../frontend/dist"

    if ($LASTEXITCODE -ne 0) {
        throw "Backend application exited with code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}