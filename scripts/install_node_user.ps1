# Downloads and extracts official Node.js 20 LTS into user profile (non-elevated)
$ErrorActionPreference = "Stop"

$nodeVersion = "v20.18.0"
$destDir = "$env:LOCALAPPDATA\Programs\NodeJS"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
$zipPath = "$destDir\node.zip"

Write-Host "Downloading Node.js $nodeVersion LTS from nodejs.org..." -ForegroundColor Cyan
$downloadUrl = "https://nodejs.org/dist/$nodeVersion/node-$nodeVersion-win-x64.zip"
Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing

Write-Host "Extracting archive to $destDir..." -ForegroundColor Cyan
Expand-Archive -Path $zipPath -DestinationPath $destDir -Force
Remove-Item -Path $zipPath -Force

$extractedFolder = Join-Path $destDir "node-$nodeVersion-win-x64"
if (Test-Path $extractedFolder) {
    Get-ChildItem -Path $extractedFolder | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $destDir -Recurse -Force
    }
    Remove-Item -Path $extractedFolder -Recurse -Force
}

$nodeExe = Join-Path $destDir "node.exe"
$npmCmd = Join-Path $destDir "npm.cmd"

Write-Host "`nVerification:" -ForegroundColor Green
$vNode = & $nodeExe --version
$vNpm = & $npmCmd --version
Write-Host "  Node.js: $vNode" -ForegroundColor Green
Write-Host "  npm:     $vNpm" -ForegroundColor Green

# Add to user PATH environment variable permanently
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$destDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$destDir;$currentPath", "User")
    Write-Host "Added $destDir to User PATH permanently." -ForegroundColor Green
}
