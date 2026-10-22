# Downloads and extracts official MinGit for Windows into user profile (non-elevated)
$ErrorActionPreference = "Stop"

$gitVersion = "v2.47.0.windows.1"
$destDir = "$env:LOCALAPPDATA\Programs\Git"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
$zipPath = "$destDir\mingit.zip"

Write-Host "Downloading MinGit $gitVersion from GitHub..." -ForegroundColor Cyan
$downloadUrl = "https://github.com/git-for-windows/git/releases/download/$gitVersion/MinGit-2.47.0-64-bit.zip"
Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing

Write-Host "Extracting archive to $destDir..." -ForegroundColor Cyan
Expand-Archive -Path $zipPath -DestinationPath $destDir -Force
Remove-Item -Path $zipPath -Force

$gitExe = Join-Path $destDir "cmd\git.exe"
if (-not (Test-Path $gitExe)) {
    $gitExe = Join-Path $destDir "bin\git.exe"
}

Write-Host "`nVerification:" -ForegroundColor Green
$vGit = & $gitExe --version
Write-Host "  Git: $vGit" -ForegroundColor Green

# Add to user PATH environment variable permanently
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$cmdDir = Join-Path $destDir "cmd"
if ($currentPath -notlike "*$cmdDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$cmdDir;$currentPath", "User")
    Write-Host "Added $cmdDir to User PATH permanently." -ForegroundColor Green
}
