<#
.SYNOPSIS
    Starts the Hybrid Multilingual Plagiarism Platform locally on native Windows.
.DESCRIPTION
    Validates Python venv, Node dependencies, port availability (8000 & 5173),
    starts FastAPI backend and Vite frontend, and provides clean console URLs
    and clean Ctrl+C shutdown.
#>

[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$Help
)

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path
    exit 0
}

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Hybrid Multilingual Plagiarism Detection Platform        " -ForegroundColor Cyan
Write-Host "  Native Windows 11 Localhost Runner (Phase 7 Final)       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "apps\backend"
$WebDir = Join-Path $RepoRoot "apps\web"
$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"

# 1. Validate Python Virtual Environment
Write-Host "`n[1/5] Checking Python Virtual Environment..." -ForegroundColor Yellow
if (-not (Test-Path $PythonExe)) {
    Write-Error "Backend virtualenv not found at: $PythonExe`nPlease run: python -m venv apps/backend/.venv and install dependencies."
}
Write-Host "      Found Python: $PythonExe" -ForegroundColor Green

# 2. Validate Frontend Dependencies
Write-Host "`n[2/5] Checking Frontend Dependencies..." -ForegroundColor Yellow
$NodeModules = Join-Path $WebDir "node_modules"
if (-not (Test-Path $NodeModules)) {
    Write-Error "node_modules not found in $WebDir`nPlease run 'npm install' inside apps/web."
}
Write-Host "      Found node_modules in $WebDir" -ForegroundColor Green

# 3. Check Port Availability
Write-Host "`n[3/5] Verifying Port Availability..." -ForegroundColor Yellow
$busy8000 = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($busy8000) {
    Write-Error "Port $BackendPort is already in use by process PID $($busy8000.OwningProcess[0]). Please free the port or specify another."
}

$busy5173 = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($busy5173) {
    Write-Error "Port $FrontendPort is already in use by process PID $($busy5173.OwningProcess[0]). Please free the port or specify another."
}
Write-Host "      Ports $BackendPort and $FrontendPort are free." -ForegroundColor Green

# 4. Launch Backend Server
Write-Host "`n[4/5] Starting FastAPI Backend on port $BackendPort..." -ForegroundColor Yellow
$BackendProc = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m uvicorn plagiarism.main:app --host 127.0.0.1 --port $BackendPort" `
    -WorkingDirectory $RepoRoot `
    -PassThru

Start-Sleep -Seconds 2
if ($BackendProc.HasExited) {
    Write-Error "Backend failed to start. Review terminal logs."
}
Write-Host "      Backend running (PID: $($BackendProc.Id))" -ForegroundColor Green

# 5. Launch Frontend Server
Write-Host "`n[5/5] Starting Vite Web Frontend on port $FrontendPort..." -ForegroundColor Yellow
$WebProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c npm run dev -- --port $FrontendPort" `
    -WorkingDirectory $WebDir `
    -PassThru

Start-Sleep -Seconds 2
if ($WebProc.HasExited) {
    Stop-Process -Id $BackendProc.Id -Force
    Write-Error "Frontend failed to start. Review terminal logs."
}
Write-Host "      Frontend running (PID: $($WebProc.Id))" -ForegroundColor Green

# Display Ready Banner
Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  PLATFORM IS READY ON LOCALHOST" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Web Application:      http://localhost:$FrontendPort" -ForegroundColor White
Write-Host "  Interactive API Docs: http://localhost:$BackendPort/docs" -ForegroundColor White
Write-Host "  Backend Health Check: http://localhost:$BackendPort/health" -ForegroundColor White
Write-Host "`nPress Ctrl+C or Enter to stop all services cleanly..." -ForegroundColor Yellow

try {
    [Console]::ReadLine()
}
finally {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    if ($BackendProc -and -not $BackendProc.HasExited) {
        Stop-Process -Id $BackendProc.Id -Force -ErrorAction SilentlyContinue
    }
    if ($WebProc -and -not $WebProc.HasExited) {
        Stop-Process -Id $WebProc.Id -Force -ErrorAction SilentlyContinue
    }
    # Clean any lingering node/uvicorn on target ports
    $lingering = Get-NetTCPConnection -LocalPort $BackendPort, $FrontendPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
    foreach ($c in $lingering) {
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    Write-Host "All local host services stopped cleanly." -ForegroundColor Green
}
