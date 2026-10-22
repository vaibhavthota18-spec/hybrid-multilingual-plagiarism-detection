# Test environment with refreshed PATH
$env:PATH = "C:\Users\vaibh\AppData\Local\Programs\NodeJS;C:\Users\vaibh\AppData\Local\Programs\Git\cmd;C:\Users\vaibh\AppData\Local\Programs\Python\Python312;C:\Users\vaibh\AppData\Local\Programs\Python\Python312\Scripts;$env:PATH"

Write-Host "=== REFRESHED RUNTIME CHECK ===" -ForegroundColor Cyan
Write-Host "Node:   " (node --version)
Write-Host "npm:    " (npm --version)
Write-Host "Git:    " (git --version)
Write-Host "Python: " (python --version)
