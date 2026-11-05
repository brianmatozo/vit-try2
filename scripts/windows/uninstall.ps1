# Vitalcer Windows Developer Uninstaller & Cleanup Wizard
$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Set-Location $RepoRoot

Write-Host "==================================================" -ForegroundColor Yellow
Write-Host "   Desinstalador y Limpieza de Vitalcer (Dev)     " -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host ""

# 1. Stop all background services
Write-Host "==> [Paso 1/3] Deteniendo servicios en ejecucion..." -ForegroundColor Cyan
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv run python scripts/windows/launcher.py --stop
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python scripts/windows/launcher.py --stop
}

# Ensure processes are terminated
if ($IsWindows -or $env:OS -eq "Windows_NT") {
    taskkill.exe /F /IM caddy.exe 2>$null
    taskkill.exe /F /IM vitalcer.exe 2>$null
}
Write-Host "    • Servicios detenidos correctamente ✅" -ForegroundColor Green

# 2. Remove Desktop Shortcuts
Write-Host "==> [Paso 2/3] Eliminando accesos directos del Escritorio..." -ForegroundColor Cyan
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$Shortcuts = @(
    (Join-Path $DesktopPath "Vitalcer POS.lnk"),
    (Join-Path $DesktopPath "Vitalcer Admin.lnk"),
    (Join-Path $DesktopPath "Vitalcer Control Panel.lnk")
)

foreach ($sc in $Shortcuts) {
    if (Test-Path $sc) {
        Remove-Item -Force $sc -ErrorAction SilentlyContinue
        Write-Host "    • Eliminado: $sc" -ForegroundColor Gray
    }
}
Write-Host "    • Accesos directos eliminados ✅" -ForegroundColor Green

# 3. Clean local data directories
Write-Host "==> [Paso 3/3] Limpieza de datos y logs..." -ForegroundColor Cyan
$DataDir = Join-Path $RepoRoot "data"
if (Test-Path $DataDir) {
    $Confirmation = Read-Host "¿Deseas eliminar la base de datos local y logs en data/? (s/N)"
    if ($Confirmation -eq "s" -or $Confirmation -eq "S") {
        Remove-Item -Recurse -Force $DataDir -ErrorAction SilentlyContinue
        Write-Host "    • Carpeta data/ eliminada ✅" -ForegroundColor Green
    } else {
        Write-Host "    • Carpeta data/ conservada." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "   Desinstalacion y limpieza completada!          " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
pause
