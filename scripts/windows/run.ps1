# PowerShell runner for Vitalcer Store Server
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Set-Location $RepoRoot

Write-Host "==================================================" -ForegroundColor Green
Write-Host " Vitalcer Store Server (PowerShell Launcher)      " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv run python scripts/windows/service_manager.py --start-all
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python scripts/windows/service_manager.py --start-all
} else {
    Write-Error "No se encontro uv ni python instalado en el sistema."
}
