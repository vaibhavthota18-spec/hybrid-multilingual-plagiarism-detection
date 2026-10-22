<#
.SYNOPSIS
    One-Command Completely Offline Classroom Launcher for Native Windows 11.
.DESCRIPTION
    Sets APP_RUNTIME_MODE=local, enforces HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1,
    validates local model cache, starts FastAPI backend (port 8000) and Vite frontend (port 5173),
    verifies backend health, displays console URLs, and provides clean Ctrl+C shutdown.
#>

[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Hybrid Multilingual Plagiarism Detection Platform        " -ForegroundColor Cyan
Write-Host "  One-Command Offline Classroom Launcher (Native Windows)  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Environment & Offline Configuration
$env:APP_RUNTIME_MODE = "local"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "apps\backend"
$WebDir = Join-Path $RepoRoot "apps\web"
$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"

# Configure Model Cache to Persistent LocalAppData or Project Storage
$LocalAppData = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::LocalApplicationData)
$PersistentCache = Join-Path $LocalAppData "plagiarism_engine\model_cache"
$RepoCache = Join-Path $RepoRoot "storage\model_cache"

if (Test-Path (Join-Path $PersistentCache "models--intfloat--multilingual-e5-small")) {
    $env:SEMANTIC_MODEL_CACHE_DIR = $PersistentCache
    $env:HF_HOME = $PersistentCache
    Write-Host "[1/5] Using persistent local model cache: $PersistentCache" -ForegroundColor Green
} elseif (Test-Path (Join-Path $RepoCache "models--intfloat--multilingual-e5-small")) {
    $env:SEMANTIC_MODEL_CACHE_DIR = $RepoCache
    $env:HF_HOME = $RepoCache
    Write-Host "[1/5] Using repository model cache: $RepoCache" -ForegroundColor Green
} else {
    Write-Error "Offline AI model cache not found. Please run .\scripts\prepare-offline-demo.ps1 once while online."
}

# 2. Check Local Prerequisites
Write-Host "`n[2/5] Checking Offline Prerequisites..." -ForegroundColor Yellow
if (-not (Test-Path $PythonExe)) {
    Write-Error "Backend Python virtualenv not found at: $PythonExe"
}
$NodeModules = Join-Path $WebDir "node_modules"
if (-not (Test-Path $NodeModules)) {
    Write-Error "Frontend node_modules not found at: $NodeModules"
}
Write-Host "      Python and Node dependencies verified locally." -ForegroundColor Green

# 3. Clean and Verify Ports
Write-Host "`n[3/5] Checking Port Availability (Ports $BackendPort, $FrontendPort)..." -ForegroundColor Yellow
$busy8000 = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($busy8000) {
    Write-Host "      Cleaning lingering process on port $BackendPort..." -ForegroundColor DarkYellow
    foreach ($p in $busy8000) {
        Stop-Process -Id $p.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

$busy5173 = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($busy5173) {
    Write-Host "      Cleaning lingering process on port $FrontendPort..." -ForegroundColor DarkYellow
    foreach ($p in $busy5173) {
        Stop-Process -Id $p.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}
Write-Host "      Ports $BackendPort and $FrontendPort are ready." -ForegroundColor Green

# 4. Launch Offline FastAPI Backend
Write-Host "`n[4/5] Launching Offline FastAPI Backend (port $BackendPort)..." -ForegroundColor Yellow
$BackendProc = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m uvicorn plagiarism.main:app --host 127.0.0.1 --port $BackendPort" `
    -WorkingDirectory $RepoRoot `
    -PassThru

# Poll for backend readiness
$BackendReady = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Milliseconds 800
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response -and $response.status -eq "ok") {
            $BackendReady = $true
            break
        }
    } catch {
        # Waiting for server
    }
}

if (-not $BackendReady) {
    if ($BackendProc -and -not $BackendProc.HasExited) {
        Stop-Process -Id $BackendProc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Error "Backend failed to report healthy status within timeout. Check logs."
}
Write-Host "      FastAPI backend is LIVE and HEALTHY (PID: $($BackendProc.Id))." -ForegroundColor Green

# 5. Launch Offline Vite Frontend
Write-Host "`n[5/5] Launching Offline React Web Frontend (port $FrontendPort)..." -ForegroundColor Yellow
$WebProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c npm run dev -- --port $FrontendPort" `
    -WorkingDirectory $WebDir `
    -PassThru

Start-Sleep -Seconds 2
if ($WebProc.HasExited) {
    Stop-Process -Id $BackendProc.Id -Force -ErrorAction SilentlyContinue
    Write-Error "Frontend failed to start. Review terminal output."
}
Write-Host "      React frontend is LIVE on port $FrontendPort (PID: $($WebProc.Id))." -ForegroundColor Green

# Display Ready Banner
Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  CLASSROOM DEMONSTRATION IS READY (100% OFFLINE)           " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Web Application:      http://localhost:$FrontendPort     " -ForegroundColor White
Write-Host "  Interactive API Docs: http://localhost:$BackendPort/docs " -ForegroundColor White
Write-Host "  Backend Health Check: http://localhost:$BackendPort/health" -ForegroundColor White
Write-Host "  Mode:                 APP_RUNTIME_MODE=local (SQLite)    " -ForegroundColor White
Write-Host "  AI Model:             intfloat/multilingual-e5-small     " -ForegroundColor White
Write-Host "  Network Connectivity: None Required (100% Localhost)     " -ForegroundColor White
Write-Host "`nPress Ctrl+C or Enter to shut down all demo services cleanly..." -ForegroundColor Yellow

try {
    [Console]::ReadLine()
}
finally {
    Write-Host "`nStopping classroom demo services..." -ForegroundColor Yellow
    if ($BackendProc -and -not $BackendProc.HasExited) {
        Stop-Process -Id $BackendProc.Id -Force -ErrorAction SilentlyContinue
    }
    if ($WebProc -and -not $WebProc.HasExited) {
        Stop-Process -Id $WebProc.Id -Force -ErrorAction SilentlyContinue
    }
    $lingering = Get-NetTCPConnection -LocalPort $BackendPort, $FrontendPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
    foreach ($c in $lingering) {
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    Write-Host "All local demonstration services stopped cleanly." -ForegroundColor Green
}
