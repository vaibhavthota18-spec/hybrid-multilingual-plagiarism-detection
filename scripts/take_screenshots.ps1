$tempDir = Join-Path $env:TEMP "edge_scr_temp"
if (-not (Test-Path $tempDir)) {
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
}

$edgeExe = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$ssDir = Join-Path (Get-Location) "data\screenshots"
if (-not (Test-Path $ssDir)) {
    New-Item -ItemType Directory -Force -Path $ssDir | Out-Null
}

$targets = @(
    @{ Name = "homepage_desktop.png"; Width = 1440; Height = 900; Url = "http://localhost:5173/" },
    @{ Name = "homepage_laptop.png"; Width = 1366; Height = 768; Url = "http://localhost:5173/" },
    @{ Name = "homepage_mobile.png"; Width = 390; Height = 844; Url = "http://localhost:5173/" },
    @{ Name = "my_documents.png"; Width = 1440; Height = 900; Url = "http://localhost:5173/#documents" },
    @{ Name = "history.png"; Width = 1440; Height = 900; Url = "http://localhost:5173/#history" },
    @{ Name = "diagnostics.png"; Width = 1440; Height = 900; Url = "http://localhost:5173/#diagnostics" },
    @{ Name = "report_preview.png"; Width = 1200; Height = 1600; Url = ("file:///" + (Get-Item "data\AOA_Syllabus_Similarity_Report.html").FullName.Replace('\', '/')) }
)

foreach ($t in $targets) {
    $outPath = Join-Path $ssDir $t.Name
    Write-Host "Capturing $($t.Name)..."
    & $edgeExe --headless=new "--user-data-dir=$tempDir" --no-sandbox "--window-size=$($t.Width),$($t.Height)" "--screenshot=$outPath" $t.Url
    Start-Sleep -Seconds 1
    if (Test-Path $outPath) {
        $item = Get-Item $outPath
        Write-Host "Captured $($t.Name): $($item.Length) bytes"
    } else {
        Write-Warning "Failed to capture $($t.Name)"
    }
}
