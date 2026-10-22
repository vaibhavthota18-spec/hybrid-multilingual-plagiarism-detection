<#
.SYNOPSIS
    Validates contracts/openapi.yaml against schema and path requirements.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Validating OpenAPI 3.1 Contract: contracts/openapi.yaml  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$projectRoot = Split-Path -Parent $PSScriptRoot
$contractPath = Join-Path $projectRoot "contracts\openapi.yaml"

if (-not (Test-Path $contractPath)) {
    Write-Error "Contract file not found at: $contractPath"
}

$rawYaml = Get-Content $contractPath -Raw

$requiredTokens = @(
    "openapi: 3.1.0",
    "/health:",
    "getHealthStatus",
    "HealthStatus:",
    "ErrorEnvelope:",
    "/documents:",
    "/analyses:",
    "/analyses/{analysis_id}/report:",
    "/analyses/{analysis_id}/findings/{finding_id}/reviews:",
    "BearerAuth:"
)

$passed = 0
$failed = 0

foreach ($token in $requiredTokens) {
    if ($rawYaml -match [regex]::Escape($token)) {
        Write-Host "  [PASS] Found required definition: $token" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  [FAIL] Missing required definition: $token" -ForegroundColor Red
        $failed++
    }
}

Write-Host "`nValidation Summary:" -ForegroundColor Cyan
Write-Host "  Passed checks: $passed" -ForegroundColor Green
Write-Host "  Failed checks: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($failed -gt 0) {
    exit 1
} else {
    Write-Host "All OpenAPI contract checks PASSED." -ForegroundColor Green
    exit 0
}
