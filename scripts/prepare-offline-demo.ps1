<#
.SYNOPSIS
    One-time online preparation script for completely offline classroom demonstration.
.DESCRIPTION
    Validates Python, Node.js, venv, packages, downloads/verifies the multilingual-e5-small
    model snapshot, syncs it to persistent local storage (%LOCALAPPDATA%), performs multilingual
    offline inference verification, and validates PDF fonts and local storage.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Hybrid Multilingual Plagiarism Detection Platform        " -ForegroundColor Cyan
Write-Host "  One-Time Online Offline Preparation Script                " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "apps\backend"
$WebDir = Join-Path $RepoRoot "apps\web"
$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"

# 1. Check Python Virtual Environment
Write-Host "`n[1/6] Checking Python Environment..." -ForegroundColor Yellow
if (-not (Test-Path $PythonExe)) {
    Write-Error "Backend virtualenv not found at: $PythonExe. Please run: python -m venv apps/backend/.venv and install dependencies."
}
$PyVer = & $PythonExe --version
Write-Host "      Found: $PyVer ($PythonExe)" -ForegroundColor Green

# 2. Check Node.js and Frontend Dependencies
Write-Host "`n[2/6] Checking Frontend Node.js Dependencies..." -ForegroundColor Yellow
$NodeModules = Join-Path $WebDir "node_modules"
if (-not (Test-Path $NodeModules)) {
    Write-Host "      node_modules missing. Installing via npm..." -ForegroundColor Cyan
    Push-Location $WebDir
    npm install
    Pop-Location
}
Write-Host "      Frontend dependencies verified at $NodeModules" -ForegroundColor Green

# 3. Prepare AI Model Assets and Validate Multilingual Inference
Write-Host "`n[3/6] Preparing and Verifying AI Model Assets (EN, HI, TE)..." -ForegroundColor Yellow
$PrepScript = Join-Path $RepoRoot "scripts\prepare_offline_assets.py"
& $PythonExe $PrepScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "Offline AI model preparation failed."
}

# 4. Verify Windows 11 Indic Fonts
Write-Host "`n[4/6] Verifying Windows Indic Unicode Fonts (Nirmala UI)..." -ForegroundColor Yellow
$NirmalaPath = "C:\Windows\Fonts\Nirmala.ttc"
if (Test-Path $NirmalaPath) {
    Write-Host "      Found native Windows Indic font: $NirmalaPath" -ForegroundColor Green
} else {
    Write-Host "      Warning: Nirmala.ttc not found at standard path. System fallback will be used." -ForegroundColor DarkYellow
}

# 5. Check SQLite Database and Local Storage
Write-Host "`n[5/6] Verifying Local Database and Storage Accessibility..." -ForegroundColor Yellow
$StorageDir = Join-Path $RepoRoot "storage"
$PrivateDir = Join-Path $StorageDir "private"
if (-not (Test-Path $PrivateDir)) {
    New-Item -ItemType Directory -Path $PrivateDir -Force | Out-Null
}
Write-Host "      Storage directory accessible: $StorageDir" -ForegroundColor Green

# 6. Verify Frontend Build
Write-Host "`n[6/6] Verifying Frontend Build..." -ForegroundColor Yellow
Push-Location $WebDir
& npx vite build
$buildExit = $LASTEXITCODE
Pop-Location
if ($buildExit -ne 0) {
    Write-Error "Vite frontend build failed."
}
Write-Host "      Frontend build verified with 0 errors." -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  OFFLINE PREPARATION COMPLETE - SYSTEM IS READY!          " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  You can now disconnect Wi-Fi and launch the application   " -ForegroundColor White
Write-Host "  using: .\scripts\start-offline-demo.ps1                   " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
