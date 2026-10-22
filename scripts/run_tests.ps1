<#
.SYNOPSIS
    Automated Test Runner for Full-Stack Deliverables.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Hybrid Plagiarism Detection Platform - Test Runner       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$projectRoot = Split-Path -Parent $PSScriptRoot
$allPassed = $true

# Ensure refreshed tools are in PATH
$env:PATH = "C:\Users\vaibh\AppData\Local\Programs\NodeJS;C:\Users\vaibh\AppData\Local\Programs\Git\cmd;C:\Users\vaibh\AppData\Local\Programs\Python\Python312;C:\Users\vaibh\AppData\Local\Programs\Python\Python312\Scripts;" + $env:PATH

# 1. Validate OpenAPI Contract
Write-Host "`n--- [1/5] Validating OpenAPI Contract ---" -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "validate_contract.ps1")
if ($LASTEXITCODE -ne 0) { $allPassed = $false }

# 2. Validate Phase 0 Architecture Consistency
Write-Host "`n--- [2/5] Validating Phase 0 Document Consistency ---" -ForegroundColor Yellow
$p0Script = Join-Path $PSScriptRoot "validate_phase0.ps1"
if (Test-Path $p0Script) {
    & $p0Script
    if ($LASTEXITCODE -ne 0) { $allPassed = $false }
}

# 3. Backend Unit and Contract Tests (Pytest in venv)
Write-Host "`n--- [3/5] Backend Test Suite (Pytest via Python 3.12 venv) ---" -ForegroundColor Yellow
$pytestExe = Join-Path $projectRoot "apps\backend\.venv\Scripts\pytest.exe"
if (Test-Path $pytestExe) {
    & $pytestExe -v (Join-Path $projectRoot "apps\backend\tests")
    if ($LASTEXITCODE -ne 0) { $allPassed = $false }
} else {
    Write-Warning "Python 3.12 venv not found at: $pytestExe"
    $allPassed = $false
}

# 4. Frontend Unit Tests and Build (Vitest and Vite)
Write-Host "`n--- [4/5] Frontend Test Suite and Build (Vitest and Vite) ---" -ForegroundColor Yellow
$webTestScript = Join-Path $PSScriptRoot "run_web_tests.ps1"
if (Test-Path $webTestScript) {
    & $webTestScript
    if ($LASTEXITCODE -ne 0) { $allPassed = $false }
}

# 5. Phase 2 End-to-End Acceptance Tests
Write-Host "`n--- [5/6] Phase 2 End-to-End Acceptance Tests ---" -ForegroundColor Yellow
$pyExe = Join-Path $projectRoot "apps\backend\.venv\Scripts\python.exe"
$e2eScript = Join-Path $PSScriptRoot "verify_phase2_e2e.py"
if ((Test-Path $pyExe) -and (Test-Path $e2eScript)) {
    & $pyExe $e2eScript
    if ($LASTEXITCODE -ne 0) { $allPassed = $false }
}

# 6. Phase 3 End-to-End Acceptance Tests
Write-Host "`n--- [6/6] Phase 3 Lexical Plagiarism Acceptance Tests ---" -ForegroundColor Yellow
$p3Script = Join-Path $PSScriptRoot "verify_phase3_e2e.py"
if ((Test-Path $pyExe) -and (Test-Path $p3Script)) {
    & $pyExe $p3Script
    if ($LASTEXITCODE -ne 0) { $allPassed = $false }
}


Write-Host "`n==========================================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "  Automated Test Runner Completed Successfully!            " -ForegroundColor Green
} else {
    Write-Host "  Test Runner Completed with Warnings or Blockers.         " -ForegroundColor Yellow
}
Write-Host "==========================================================" -ForegroundColor Cyan
