<#
.SYNOPSIS
    Starts the full-stack Hybrid Plagiarism Detection Platform locally via Docker Compose.
.DESCRIPTION
    Checks container runtime prerequisites, orchestrates db, redis, api, worker, and web services,
    and applies schema migrations.
#>

[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$Detached = $true,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Hybrid Multilingual Plagiarism Platform — Local Runner   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Check Docker availability
$dockerCmd = Get-Command "docker" -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Warning "Docker is not detected in your PATH."
    Write-Host "Please install Docker Desktop or ensure WSL2 Docker is running." -ForegroundColor Yellow
    Write-Host "`nTo run services manually on host without containers:" -ForegroundColor White
    Write-Host "  1. Start local PostgreSQL 16 (with pgvector) on port 5432"
    Write-Host "  2. Start local Redis on port 6379"
    Write-Host "  3. In apps/backend: pip install -e . ; alembic upgrade head ; uvicorn plagiarism.main:app --port 8000"
    Write-Host "  4. In apps/web: npm install ; npm run dev"
    exit 1
}

$composeFile = Join-Path $PSScriptRoot "..\compose.yml"
if (-not (Test-Path $composeFile)) {
    Write-Error "compose.yml not found at: $composeFile"
}

$cmdArgs = @("compose", "-f", $composeFile, "up")
if ($Build) {
    $cmdArgs += "--build"
}
if ($Detached) {
    $cmdArgs += "-d"
}

Write-Host "Executing: docker $($cmdArgs -join ' ')" -ForegroundColor Green
& docker @cmdArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker Compose failed to start services. Review logs with: docker compose logs"
}

Write-Host "`nServices started successfully:" -ForegroundColor Green
Write-Host "  - Web Frontend:   http://localhost:3000" -ForegroundColor Cyan
Write-Host "  - Backend API:    http://localhost:8000" -ForegroundColor Cyan
Write-Host "  - OpenAPI Docs:   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  - Health Probe:   http://localhost:8000/api/v1/health" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
