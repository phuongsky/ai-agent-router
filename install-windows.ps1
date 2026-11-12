param(
  [string]$InstallPath = (Get-Location).Path
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw "Python launcher 'py' not found. Install Python 3.11+ first." }
py -3.11 -m venv (Join-Path $InstallPath ".venv")
$Python = Join-Path $InstallPath ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -e "${InstallPath}[dev]"
Write-Host "AI Requirement Router installed at $InstallPath" -ForegroundColor Green
Write-Host "Next: arr register --id my-project --name MyProject --path C:\Projects\MyProject" -ForegroundColor Cyan
