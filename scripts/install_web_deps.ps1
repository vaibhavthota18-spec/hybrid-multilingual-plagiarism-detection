# Install frontend dependencies with proper PATH and retry handling
$ErrorActionPreference = "Stop"
$env:PATH = "C:\Users\vaibh\AppData\Local\Programs\NodeJS;C:\Users\vaibh\AppData\Local\Programs\Git\cmd;$env:PATH"

$webDir = Resolve-Path (Join-Path $PSScriptRoot "..\apps\web")
Set-Location $webDir

Write-Host "Running npm install in $webDir..." -ForegroundColor Cyan
& npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nnpm dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Error "npm install exited with code $LASTEXITCODE"
}
