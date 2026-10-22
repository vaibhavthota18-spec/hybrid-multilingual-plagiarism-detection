# Install Python 3.12 virtual environment dependencies
$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot "..\apps\backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Creating Python 3.12 virtual environment..." -ForegroundColor Cyan
    & "C:\Users\vaibh\AppData\Local\Programs\Python\Python312\python.exe" -m venv (Join-Path $PSScriptRoot "..\apps\backend\.venv")
}

Write-Host "Upgrading pip in venv..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip

Write-Host "Installing backend in editable mode and testing tools..." -ForegroundColor Cyan
& $venvPython -m pip install -e (Join-Path $PSScriptRoot "..\apps\backend")
& $venvPython -m pip install pytest pytest-asyncio httpx

Write-Host "`nBackend virtual environment dependencies successfully installed!" -ForegroundColor Green
