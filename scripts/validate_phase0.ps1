# ==============================================================================
# Phase 0 Automated Blueprint & Contract Validation Script
# Project: Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System
# ==============================================================================

param(
    [string]$ProjectRoot = "C:\Users\vaibh\OneDrive\Documents\plagarism engine"
)

$ErrorActionPreference = "Continue"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " STARTING AUTOMATED PHASE 0 VALIDATION CHECKS" -ForegroundColor Cyan
Write-Host " Target Directory: $ProjectRoot" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$TotalChecks = 0
$PassedChecks = 0
$FailedChecks = 0
$Warnings = 0

function Assert-Check {
    param(
        [string]$Description,
        [bool]$Condition,
        [string]$FailureMessage = ""
    )
    $script:TotalChecks++
    if ($Condition) {
        $script:PassedChecks++
        Write-Host " [PASS] $Description" -ForegroundColor Green
    } else {
        $script:FailedChecks++
        Write-Host " [FAIL] $Description" -ForegroundColor Red
        if ($FailureMessage) {
            Write-Host "        Reason: $FailureMessage" -ForegroundColor Yellow
        }
    }
}

# 1. Project Root Directory Verification
Assert-Check -Description "Project root directory exists" `
    -Condition (Test-Path -LiteralPath $ProjectRoot) `
    -FailureMessage "Project root directory does not exist at $ProjectRoot"

# 2. Check All Required Phase 0 Files
$RequiredFiles = @(
    "README.md",
    "AGENTS.md",
    ".gitignore",
    ".editorconfig",
    ".env.example",
    "docs/phases/phase-00/repository-audit.md",
    "docs/00-product/project-charter.md",
    "docs/00-product/scope-and-features.md",
    "docs/00-product/user-journeys.md",
    "docs/00-product/requirements.md",
    "docs/00-product/terminology-and-assumptions.md",
    "docs/01-architecture/system-context.md",
    "docs/01-architecture/component-design.md",
    "docs/01-architecture/processing-and-sequences.md",
    "docs/01-architecture/module-contracts.md",
    "docs/01-architecture/repository-blueprint.md",
    "docs/01-architecture/technology-decisions.md",
    "docs/01-architecture/adrs/ADR-0001-modular-monolith.md",
    "docs/01-architecture/adrs/ADR-0002-api-contracts.md",
    "docs/01-architecture/adrs/ADR-0003-hybrid-detection.md",
    "docs/01-architecture/adrs/ADR-0004-vector-search.md",
    "docs/01-architecture/adrs/ADR-0005-ai-model-strategy.md",
    "docs/01-architecture/adrs/ADR-0006-storage-and-privacy.md",
    "docs/01-architecture/adrs/ADR-0007-background-jobs.md",
    "docs/01-architecture/adrs/ADR-0008-evaluation-first.md",
    "docs/02-api/api-design.md",
    "docs/02-api/authorization-and-errors.md",
    "contracts/openapi.yaml",
    "contracts/README.md",
    "docs/03-data/data-model.md",
    "docs/03-data/offsets-and-scoring.md",
    "docs/03-data/indexes-and-lifecycle.md",
    "docs/04-security/threat-model.md",
    "docs/04-security/privacy-access-retention.md",
    "docs/05-evaluation/benchmark-plan.md",
    "docs/05-evaluation/dataset-and-annotation.md",
    "docs/05-evaluation/metrics-and-acceptance.md",
    "docs/05-evaluation/model-selection.md",
    "docs/06-operations/deployment-plan.md",
    "docs/06-operations/environment-and-observability.md",
    "docs/06-operations/cost-and-capacity.md",
    "docs/phases/phase-00/requirements-traceability.md",
    "docs/phases/phase-00/risk-register.md",
    "docs/phases/phase-00/validation-report.md",
    "docs/phases/phase-00/phase0-completion.md",
    "docs/phases/phase-00/phase1-handoff.md",
    "scripts/validate_openapi.ps1"
)

Write-Host "`n--- Verifying File Existence & Content Sizing ---" -ForegroundColor Cyan
foreach ($relPath in $RequiredFiles) {
    $fullPath = Join-Path -Path $ProjectRoot -ChildPath $relPath
    $exists = Test-Path -LiteralPath $fullPath
    if ($exists) {
        $item = Get-Item -LiteralPath $fullPath
        $hasContent = $item.Length -ge 100
        Assert-Check -Description "File exists and is non-empty: $relPath ($($item.Length) bytes)" `
            -Condition $hasContent `
            -FailureMessage "File is empty or less than 100 bytes"
    } else {
        Assert-Check -Description "File exists: $relPath" -Condition $false -FailureMessage "File not found"
    }
}

# 3. OpenAPI Contract Structural Verification
Write-Host "`n--- Verifying OpenAPI 3.1 Contract Structure ---" -ForegroundColor Cyan
$openApiPath = Join-Path -Path $ProjectRoot -ChildPath "contracts/openapi.yaml"
if (Test-Path -LiteralPath $openApiPath) {
    $openApiContent = Get-Content -LiteralPath $openApiPath -Raw
    Assert-Check -Description "OpenAPI declares version 3.1.0" `
        -Condition ($openApiContent -match "openapi:\s*3\.1\.0")
    Assert-Check -Description "OpenAPI declares /documents endpoint" `
        -Condition ($openApiContent -match "/documents:")
    Assert-Check -Description "OpenAPI declares /analyses endpoint" `
        -Condition ($openApiContent -match "/analyses:")
    Assert-Check -Description "OpenAPI declares /collections endpoint" `
        -Condition ($openApiContent -match "/collections:")
    Assert-Check -Description "OpenAPI declares /health endpoint" `
        -Condition ($openApiContent -match "/health:")
    Assert-Check -Description "OpenAPI includes three comparison modes (direct, one_to_many, corpus)" `
        -Condition ($openApiContent -match "direct" -and $openApiContent -match "one_to_many" -and $openApiContent -match "corpus")
    Assert-Check -Description "OpenAPI includes job status states (queued, processing, completed, failed, cancelled)" `
        -Condition ($openApiContent -match "queued" -and $openApiContent -match "processing" -and $openApiContent -match "completed" -and $openApiContent -match "failed" -and $openApiContent -match "cancelled")
}

# 4. Requirements Consistency & Traceability Check
Write-Host "`n--- Verifying Requirements Traceability Matrix ---" -ForegroundColor Cyan
$reqsPath = Join-Path -Path $ProjectRoot -ChildPath "docs/00-product/requirements.md"
$rtmPath = Join-Path -Path $ProjectRoot -ChildPath "docs/phases/phase-00/requirements-traceability.md"
if ((Test-Path -LiteralPath $reqsPath) -and (Test-Path -LiteralPath $rtmPath)) {
    $reqsContent = Get-Content -LiteralPath $reqsPath -Raw
    $rtmContent = Get-Content -LiteralPath $rtmPath -Raw
    
    $CoreIds = @(
        "FR-DOC-001", "FR-DOC-002", "FR-DOC-003", "FR-DOC-004", "FR-DOC-005",
        "FR-MODE-001", "FR-MODE-002", "FR-MODE-003",
        "FR-DET-001", "FR-DET-002", "FR-DET-003", "FR-DET-004", "FR-DET-005", "FR-DET-006", "FR-DET-007",
        "FR-REP-001", "FR-REP-002", "FR-REP-003", "FR-REP-004",
        "FR-COL-001", "FR-COL-002",
        "NFR-SEC-001", "NFR-SEC-002", "NFR-PRIV-001", "NFR-PERF-001", "NFR-PERF-002",
        "NFR-SCAL-001", "NFR-REL-001", "NFR-REL-002", "NFR-A11Y-001", "NFR-OBS-001", "NFR-DEP-001"
    )
    
    $AllIdsFoundInRtm = $true
    foreach ($id in $CoreIds) {
        if (-not ($rtmContent -match $id)) {
            $AllIdsFoundInRtm = $false
            Write-Host "        Missing requirement in RTM: $id" -ForegroundColor Red
        }
    }
    Assert-Check -Description "All 32 core requirements traced in RTM" -Condition $AllIdsFoundInRtm
}

# 5. Strict Phase 0 Boundary Guard: Verify NO Application Code Was Generated
Write-Host "`n--- Verifying Phase 0 Boundary Isolation ---" -ForegroundColor Cyan
$forbiddenCodeFiles = Get-ChildItem -LiteralPath $ProjectRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { 
        $_.Extension -in @('.py', '.ts', '.tsx', '.js', '.jsx') -and 
        $_.FullName -notmatch "scripts" -and 
        $_.FullName -notmatch "docs" -and
        $_.FullName -notmatch "apps" -and
        $_.FullName -notmatch "node_modules" -and
        $_.FullName -notmatch "\.venv"
    }

if ($null -eq $forbiddenCodeFiles -or $forbiddenCodeFiles.Count -eq 0) {
    Assert-Check -Description "Zero application source code files created in Phase 0" -Condition $true
} else {
    Assert-Check -Description "Zero application source code files created in Phase 0" -Condition $false `
        -FailureMessage "Found premature code files: $($forbiddenCodeFiles.Name -join ', ')"
}

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host " VALIDATION SUMMARY:" -ForegroundColor Cyan
Write-Host " Total Checks:  $TotalChecks" -ForegroundColor White
Write-Host " Passed Checks: $PassedChecks" -ForegroundColor Green
Write-Host " Failed Checks: $FailedChecks" -ForegroundColor $(if ($FailedChecks -eq 0) { "Green" } else { "Red" })
Write-Host "======================================================================" -ForegroundColor Cyan

if ($FailedChecks -eq 0) {
    Write-Host " PHASE 0 AUTOMATED VALIDATION STATUS: PASS" -ForegroundColor Green
    exit 0
} else {
    Write-Host " PHASE 0 AUTOMATED VALIDATION STATUS: FAIL" -ForegroundColor Red
    exit 1
}
