# Run all frontend tests and production build
$ErrorActionPreference = "Stop"
$env:PATH = "C:\Users\vaibh\AppData\Local\Programs\NodeJS;C:\Users\vaibh\AppData\Local\Programs\Git\cmd;$env:PATH"

$origLocation = Get-Location
$webDir = Resolve-Path (Join-Path $PSScriptRoot "..\apps\web")
try {
    Set-Location $webDir

    Write-Host "=== [1/3] TypeScript Typecheck ===" -ForegroundColor Cyan
    & npm run typecheck

    Write-Host "`n=== [2/3] Vitest Unit Tests ===" -ForegroundColor Cyan
    & npm run test

    Write-Host "`n=== [3/3] Production Bundle Build ===" -ForegroundColor Cyan
    & npm run build

    Write-Host "`nAll frontend verification steps PASSED!" -ForegroundColor Green
} finally {
    Set-Location $origLocation
}
