# ==============================================================================
# Independent OpenAPI 3.1 Specification Validator
# Project: Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System
# ==============================================================================

param(
    [string]$SpecPath = "C:\Users\vaibh\OneDrive\Documents\plagarism engine\contracts\openapi.yaml"
)

$ErrorActionPreference = "Continue"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " RUNNING INDEPENDENT OPENAPI 3.1 SPECIFICATION VALIDATION" -ForegroundColor Cyan
Write-Host " Target Specification: $SpecPath" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

if (-not (Test-Path -LiteralPath $SpecPath)) {
    Write-Host "[FATAL] OpenAPI specification not found at $SpecPath" -ForegroundColor Red
    exit 1
}

$content = Get-Content -LiteralPath $SpecPath -Raw
$TotalChecks = 0
$PassedChecks = 0
$FailedChecks = 0

function Assert-Spec {
    param(
        [string]$Description,
        [bool]$Condition,
        [string]$FailureDetail = ""
    )
    $script:TotalChecks++
    if ($Condition) {
        $script:PassedChecks++
        Write-Host " [PASS] $Description" -ForegroundColor Green
    } else {
        $script:FailedChecks++
        Write-Host " [FAIL] $Description" -ForegroundColor Red
        if ($FailureDetail) {
            Write-Host "        Reason: $FailureDetail" -ForegroundColor Yellow
        }
    }
}

# 1. Root & Version Integrity
Write-Host "`n--- 1. Root Structure & Version Integrity ---" -ForegroundColor Cyan
Assert-Spec -Description "OpenAPI specifies exact version 3.1.0" `
    -Condition ($content -match "(?m)^openapi:\s*3\.1\.0\s*$")
Assert-Spec -Description "Root info object contains title and version" `
    -Condition ($content -match "(?m)^info:" -and $content -match "title:" -and $content -match "version:")
Assert-Spec -Description "Root components block defined" `
    -Condition ($content -match "(?m)^components:")
Assert-Spec -Description "Root paths block defined" `
    -Condition ($content -match "(?m)^paths:")

# 2. Comprehensive $ref Reference Resolution
Write-Host "`n--- 2. Schema `$ref` Target Resolution ---" -ForegroundColor Cyan
$refs = [regex]::Matches($content, '\$ref:\s*[''"]?([^''"\s]+)[''"]?') | 
    ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique

$unresolvedRefs = @()
foreach ($ref in $refs) {
    if ($ref.StartsWith('#/components/')) {
        $parts = $ref.Substring('#/components/'.Length).Split('/')
        $category = $parts[0]
        $targetName = $parts[1]
        $pattern = "(?m)^\s{4}${targetName}:"
        if ($content -notmatch $pattern) {
            $unresolvedRefs += "$ref ($category -> $targetName)"
        }
    } else {
        $unresolvedRefs += "$ref (External/Unrecognized URI format)"
    }
}

Assert-Spec -Description "All $($refs.Count) internal `$ref targets resolve successfully" `
    -Condition ($unresolvedRefs.Count -eq 0) `
    -FailureDetail ($unresolvedRefs -join ', ')

# 3. Path Parameters & URL Invariants
Write-Host "`n--- 3. Path Parameter Matching & Operation Integrity ---" -ForegroundColor Cyan
$pathBlocks = [regex]::Matches($content, '(?m)^\s{2}(/[^:\s]+):')
$allPathParamsValid = $true
$invalidPaths = @()

foreach ($match in $pathBlocks) {
    $pathUrl = $match.Groups[1].Value
    $paramNames = [regex]::Matches($pathUrl, '\{([^}]+)\}') | ForEach-Object { $_.Groups[1].Value }
    foreach ($pName in $paramNames) {
        $escapedPath = [regex]::Escape($pathUrl)
        $escapedParam = [regex]::Escape($pName)
        $paramDefPattern = "(?s)\s{2}" + $escapedPath + ":.*?name:\s*" + $escapedParam + ".*?in:\s*path.*?required:\s*true"
        if ($content -notmatch $paramDefPattern) {
            $allPathParamsValid = $false
            $invalidPaths += "Path '$pathUrl' missing parameter definition for '{$pName}'"
        }
    }
}

Assert-Spec -Description "All path parameters in URL templates are explicitly declared with in: path and required: true" `
    -Condition $allPathParamsValid `
    -FailureDetail ($invalidPaths -join '; ')

# 4. Operation Methods & Response Codes
Write-Host "`n--- 4. HTTP Verbs & Success Responses ---" -ForegroundColor Cyan
$operations = @(
    @{ Path = "/health"; Method = "get"; OpId = "getHealthStatus"; ExpectedSuccess = "200" },
    @{ Path = "/documents"; Method = "post"; OpId = "uploadDocument"; ExpectedSuccess = "201" },
    @{ Path = "/documents"; Method = "get"; OpId = "listDocuments"; ExpectedSuccess = "200" },
    @{ Path = "/documents/{document_id}"; Method = "get"; OpId = "getDocument"; ExpectedSuccess = "200" },
    @{ Path = "/documents/{document_id}"; Method = "delete"; OpId = "deleteDocument"; ExpectedSuccess = "204" },
    @{ Path = "/collections"; Method = "post"; OpId = "createCollection"; ExpectedSuccess = "201" },
    @{ Path = "/collections"; Method = "get"; OpId = "listCollections"; ExpectedSuccess = "200" },
    @{ Path = "/collections/{collection_id}"; Method = "get"; OpId = "getCollection"; ExpectedSuccess = "200" },
    @{ Path = "/collections/{collection_id}/documents"; Method = "post"; OpId = "addDocumentToCollection"; ExpectedSuccess = "202" },
    @{ Path = "/analyses"; Method = "post"; OpId = "createAnalysis"; ExpectedSuccess = "202" },
    @{ Path = "/analyses"; Method = "get"; OpId = "listAnalyses"; ExpectedSuccess = "200" },
    @{ Path = "/analyses/{analysis_id}"; Method = "get"; OpId = "getAnalysisResults"; ExpectedSuccess = "200" },
    @{ Path = "/analyses/{analysis_id}/status"; Method = "get"; OpId = "getAnalysisStatus"; ExpectedSuccess = "200" },
    @{ Path = "/analyses/{analysis_id}/cancel"; Method = "post"; OpId = "cancelAnalysis"; ExpectedSuccess = "200" },
    @{ Path = "/analyses/{analysis_id}/report"; Method = "get"; OpId = "downloadAnalysisReport"; ExpectedSuccess = "200" },
    @{ Path = "/analyses/{analysis_id}/findings/{finding_id}/reviews"; Method = "post"; OpId = "submitFindingReview"; ExpectedSuccess = "200" }
)

$opsAllValid = $true
$failedOps = @()
foreach ($op in $operations) {
    $p = $op.Path
    $m = $op.Method
    $opId = $op.OpId
    $code = $op.ExpectedSuccess
    
    $escapedP = [regex]::Escape($p)
    $escapedM = [regex]::Escape($m)
    $escapedOpId = [regex]::Escape($opId)
    $checkPattern = "(?s)\s{2}" + $escapedP + ":.*?\s{4}" + $escapedM + ":.*?operationId:\s*" + $escapedOpId + ".*?'" + $code + "':"
    if ($content -notmatch $checkPattern) {
        $opsAllValid = $false
        $failedOps += "$m $p ($opId -> $code)"
    }
}

Assert-Spec -Description "All 16 planned operations declare valid operationIds and expected 2xx response codes" `
    -Condition $opsAllValid `
    -FailureDetail ($failedOps -join '; ')

# 5. Domain Enum Constellations
Write-Host "`n--- 5. Domain Enum Invariants ---" -ForegroundColor Cyan
Assert-Spec -Description "Comparison modes enum covers: direct, one_to_many, corpus" `
    -Condition ($content -match "enum:\s*\[direct,\s*one_to_many,\s*corpus\]")

Assert-Spec -Description "Job states enum covers: queued, processing, completed, failed, cancelled" `
    -Condition ($content -match "enum:\s*\[queued,\s*processing,\s*completed,\s*failed,\s*cancelled\]")

Assert-Spec -Description "Match category enum covers: exact_copy, near_exact_rewrite, paraphrase, potential_translation" `
    -Condition ($content -match "enum:\s*\[exact_copy,\s*near_exact_rewrite,\s*paraphrase,\s*potential_translation\]")

Assert-Spec -Description "Human review labels enum covers: VALID_CITATION, SUSPECTED_PLAGIARISM, FALSE_POSITIVE, IGNORED" `
    -Condition ($content -match "enum:\s*\[VALID_CITATION,\s*SUSPECTED_PLAGIARISM,\s*FALSE_POSITIVE,\s*IGNORED\]")

# 6. Report Download Binary Payload Semantics
Write-Host "`n--- 6. Binary Report Download Semantics ---" -ForegroundColor Cyan
Assert-Spec -Description "Report download endpoint specifies application/pdf with format: binary" `
    -Condition ($content -match "(?s)/analyses/\{analysis_id\}/report:.*?application/pdf:.*?format:\s*binary")

# 7. Authentication & Security Schemes
Write-Host "`n--- 7. Security Schemes & Authentication ---" -ForegroundColor Cyan
Assert-Spec -Description "BearerAuth security scheme defined with type: http, scheme: bearer, bearerFormat: JWT" `
    -Condition ($content -match "(?s)BearerAuth:.*?type:\s*http.*?scheme:\s*bearer.*?bearerFormat:\s*JWT")

# Summary
Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host " OPENAPI 3.1 VALIDATION SUMMARY:" -ForegroundColor Cyan
Write-Host " Total Assertions: $TotalChecks" -ForegroundColor White
Write-Host " Passed:           $PassedChecks" -ForegroundColor Green
Write-Host " Failed:           $FailedChecks" -ForegroundColor $(if ($FailedChecks -eq 0) { "Green" } else { "Red" })
Write-Host "======================================================================" -ForegroundColor Cyan

if ($FailedChecks -eq 0) {
    Write-Host " OPENAPI 3.1 SPECIFICATION STATUS: PASS" -ForegroundColor Green
    exit 0
} else {
    Write-Host " OPENAPI 3.1 SPECIFICATION STATUS: FAIL" -ForegroundColor Red
    exit 1
}
