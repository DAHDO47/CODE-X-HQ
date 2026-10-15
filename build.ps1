# Baut CODE/X HQ nach dist\ProjectHQ\ProjectHQ.exe
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "[1/2] Tests" -ForegroundColor Green
py -3.12 -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests fehlgeschlagen - Build abgebrochen." }

Write-Host "[2/2] PyInstaller" -ForegroundColor Green
py -3.12 -m PyInstaller ProjectHQ.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "Build fehlgeschlagen." }

Write-Host ""
Write-Host "Fertig: $PSScriptRoot\dist\ProjectHQ\ProjectHQ.exe" -ForegroundColor Green
