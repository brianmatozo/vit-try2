# Vitalcer Automated Packaging & Installer Builder Script for Windows
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Set-Location $RepoRoot

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   Compilador y Creador de Instalador de Vitalcer        " -ForegroundColor Green
Write-Host "   (PyInstaller --onedir + Inno Setup lzma2)              " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""

# 1. Locate Inno Setup Compiler (ISCC.exe)
Write-Host "==> [Paso 1/5] Verificando compilador Inno Setup (ISCC.exe)..." -ForegroundColor Cyan
$IsccPath = $null
if (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue) {
    $IsccPath = "ISCC.exe"
} else {
    $StandardLocations = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($loc in $StandardLocations) {
        if (Test-Path $loc) {
            $IsccPath = $loc
            break
        }
    }
}

if (-not $IsccPath) {
    Write-Warning "Inno Setup 6 no encontrado en las rutas habituales."
    Write-Host "    Descarga e instala Inno Setup 6 desde: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host "    o ejecuta: winget install JRSoftware.InnoSetup" -ForegroundColor Yellow
    exit 1
}
Write-Host "    • Inno Setup encontrado: $IsccPath ✅" -ForegroundColor Green

# 2. Ensure Caddy & PostgreSQL 18 portable binaries exist in tools/
Write-Host "==> [Paso 2/5] Verificando binarios portables en tools/..." -ForegroundColor Cyan
$ToolsDir = Join-Path $RepoRoot "tools"
New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null

$CaddyExe = Join-Path $ToolsDir "caddy\caddy.exe"
if (-not (Test-Path $CaddyExe)) {
    Write-Host "    • Descargando Caddy portable..." -ForegroundColor Yellow
    $CaddyDir = Join-Path $ToolsDir "caddy"
    New-Item -ItemType Directory -Force -Path $CaddyDir | Out-Null
    $CaddyZip = Join-Path $CaddyDir "caddy.zip"
    $CaddyUrl = "https://github.com/caddyserver/caddy/releases/download/v2.8.4/caddy_2.8.4_windows_amd64.zip"
    $oldProgress = $ProgressPreference
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $CaddyUrl -OutFile $CaddyZip -UseBasicParsing
    $ProgressPreference = $oldProgress
    Expand-Archive -Path $CaddyZip -DestinationPath $CaddyDir -Force
    Remove-Item $CaddyZip -Force -ErrorAction SilentlyContinue
    Write-Host "    • Caddy descargado en $CaddyExe ✅" -ForegroundColor Green
} else {
    Write-Host "    • Caddy disponible ✅" -ForegroundColor Green
}

$LocalInitDb = Join-Path $ToolsDir "pgsql\bin\initdb.exe"
if (-not (Test-Path $LocalInitDb)) {
    Write-Host "    • Descargando PostgreSQL 18 portable (EnterpriseDB x64)..." -ForegroundColor Yellow
    $PgZip = Join-Path $ToolsDir "pgsql.zip"
    $PgUrl = "https://get.enterprisedb.com/postgresql/postgresql-18.6-5-windows-x64-binaries.zip"
    $oldProgress = $ProgressPreference
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $PgUrl -OutFile $PgZip -UseBasicParsing
    $ProgressPreference = $oldProgress
    Expand-Archive -Path $PgZip -DestinationPath $ToolsDir -Force
    Remove-Item $PgZip -Force -ErrorAction SilentlyContinue
    Write-Host "    • PostgreSQL 18 portable descargado y extraído ✅" -ForegroundColor Green
} else {
    Write-Host "    • PostgreSQL 18 portable disponible ✅" -ForegroundColor Green
}

# 3. Build Static Frontends (Admin & POS)
Write-Host "==> [Paso 3/5] Compilando aplicaciones frontend estaticas..." -ForegroundColor Cyan
uv run python scripts/api_export.py
pnpm --filter @vitalcer/api generate
pnpm -r --filter "./apps/*" build
node scripts/compress_static.mjs
Write-Host "    • Frontends compilados y pre-comprimidos con Brotli/Gzip ✅" -ForegroundColor Green

# 4. Compile Python Backend & GUI Supervisor with PyInstaller
Write-Host "==> [Paso 4/5] Empaquetando backend y GUI con PyInstaller..." -ForegroundColor Cyan
uv run pyinstaller scripts/windows/vitalcer.spec --clean -y
Write-Host "    • Binarios compilados en dist\vitalcer_control\ ✅" -ForegroundColor Green

# 5. Compile Inno Setup Installer
Write-Host "==> [Paso 5/5] Generando instalador final con Inno Setup..." -ForegroundColor Cyan
$IssScript = Join-Path $RepoRoot "scripts\windows\vitalcer.iss"
& $IsccPath $IssScript

$InstallerPath = Join-Path $RepoRoot "dist\vitalcer-setup-x64.exe"
if (Test-Path $InstallerPath) {
    $SizeMb = [math]::Round((Get-Item $InstallerPath).Length / 1MB, 2)
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "   Instalador generado con éxito!                         " -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "Archivo: $InstallerPath" -ForegroundColor White
    Write-Host "Tamaño:  $SizeMb MB" -ForegroundColor White
    Write-Host ""
} else {
    Write-Error "No se pudo generar el instalador en $InstallerPath"
}
