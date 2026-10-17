# Vitalcer Windows Automated Setup & Installer Wizard
$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Set-Location $RepoRoot

Write-Host "==================================================" -ForegroundColor Green
Write-Host "   Instalador de Vitalcer para Windows            " -ForegroundColor Green
Write-Host "   (XAMPP-Style Stack: Postgres + FastAPI + Caddy)" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# 1. Check or install uv (Astral Python Package Manager)
Write-Host "==> [Paso 1/5] Verificando gestor de Python (uv)..." -ForegroundColor Cyan
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "    • uv no encontrado. Descargando e instalando uv..." -ForegroundColor Yellow
    try {
        powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        $localBin = Join-Path $env:USERPROFILE ".local\bin"
        $cargoBin = Join-Path $env:USERPROFILE ".cargo\bin"
        if (Test-Path $localBin) { $env:Path = "$localBin;$env:Path" }
        if (Test-Path $cargoBin) { $env:Path = "$cargoBin;$env:Path" }
    } catch {
        Write-Warning "No se pudo auto-instalar uv. Asegurate de tener Python 3.12+ instalado."
    }
} else {
    Write-Host "    • uv encontrado correctamente: $(Get-Command uv | Select-Object -ExpandProperty Source)" -ForegroundColor Green
}

# 2. Check or download Caddy for Windows
Write-Host "==> [Paso 2/5] Verificando servidor web Caddy..." -ForegroundColor Cyan
$CaddyDir = Join-Path $RepoRoot "tools\caddy"
$CaddyExe = Join-Path $CaddyDir "caddy.exe"
if (-not (Test-Path $CaddyExe) -and -not (Get-Command caddy -ErrorAction SilentlyContinue)) {
    Write-Host "    • Descargando Caddy para Windows (AMD64)..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $CaddyDir | Out-Null
    $CaddyZip = Join-Path $CaddyDir "caddy.zip"
    $CaddyUrl = "https://github.com/caddyserver/caddy/releases/download/v2.8.4/caddy_2.8.4_windows_amd64.zip"
    try {
        Invoke-WebRequest -Uri $CaddyUrl -OutFile $CaddyZip -UseBasicParsing
        Expand-Archive -Path $CaddyZip -DestinationPath $CaddyDir -Force
        Remove-Item $CaddyZip -Force -ErrorAction SilentlyContinue
        Write-Host "    • Caddy descargado en $CaddyExe ✅" -ForegroundColor Green
    } catch {
        Write-Warning "No se pudo descargar Caddy automaticamente. Puedes instalarlo con 'winget install caddy'."
    }
} else {
    Write-Host "    • Caddy disponible ✅" -ForegroundColor Green
}

# 3. Check or download PostgreSQL for Windows & initialize cluster
Write-Host "==> [Paso 3/5] Verificando PostgreSQL 18 portable..." -ForegroundColor Cyan
$PgToolsDir = Join-Path $RepoRoot "tools\pgsql"
$LocalInitDb = Join-Path $PgToolsDir "bin\initdb.exe"
$LocalPgCtl = Join-Path $PgToolsDir "bin\pg_ctl.exe"
$LocalCreateDb = Join-Path $PgToolsDir "bin\createdb.exe"

if (-not (Test-Path $LocalInitDb)) {
    Write-Host "    • Descargando PostgreSQL 18 portable para Windows (AMD64)..." -ForegroundColor Yellow
    $ToolsDir = Join-Path $RepoRoot "tools"
    New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
    $PgZip = Join-Path $ToolsDir "pgsql.zip"
    $PgUrl = "https://get.enterprisedb.com/postgresql/postgresql-18.6-5-windows-x64-binaries.zip"
    $oldProgress = $ProgressPreference
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $PgUrl -OutFile $PgZip -UseBasicParsing
        $ProgressPreference = $oldProgress
        Expand-Archive -Path $PgZip -DestinationPath $ToolsDir -Force
        Remove-Item $PgZip -Force -ErrorAction SilentlyContinue
        Write-Host "    • PostgreSQL 18 descargado y extraído en $PgToolsDir ✅" -ForegroundColor Green
    } catch {
        $ProgressPreference = $oldProgress
        Write-Warning "No se pudo auto-descargar PostgreSQL portable: $_"
    }
} else {
    Write-Host "    • PostgreSQL portable disponible ✅" -ForegroundColor Green
}

$PgDataDir = Join-Path $RepoRoot "data\postgres"
$PgVersionFile = Join-Path $PgDataDir "PG_VERSION"

if (-not (Test-Path $PgVersionFile)) {
    $InitDbCmd = $null
    if (Test-Path $LocalInitDb) {
        $InitDbCmd = $LocalInitDb
    } elseif (Get-Command initdb -ErrorAction SilentlyContinue) {
        $InitDbCmd = "initdb"
    }

    if ($InitDbCmd) {
        Write-Host "    • Inicializando cluster de base de datos en $PgDataDir..." -ForegroundColor Yellow
        New-Item -ItemType Directory -Force -Path $PgDataDir | Out-Null
        & $InitDbCmd -D $PgDataDir -U vitalcer --auth=trust --encoding=UTF8
        Write-Host "    • Cluster PostgreSQL inicializado con usuario 'vitalcer' ✅" -ForegroundColor Green

        # Ensure database 'vitalcer' is created
        if ((Test-Path $LocalPgCtl) -and (Test-Path $LocalCreateDb)) {
            Write-Host "    • Creando base de datos inicial 'vitalcer'..." -ForegroundColor Yellow
            $LogsDir = Join-Path $RepoRoot "data\logs"
            New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null
            $TempLog = Join-Path $LogsDir "postgres.log"
            & $LocalPgCtl -D $PgDataDir -l $TempLog -w start
            Start-Sleep -Seconds 1
            & $LocalCreateDb -U vitalcer -h 127.0.0.1 vitalcer 2>$null
            & $LocalPgCtl -D $PgDataDir -m fast stop
            Write-Host "    • Base de datos 'vitalcer' lista ✅" -ForegroundColor Green
        }
    } else {
        Write-Host "    • Nota: Si usas el servicio de Windows existente o Docker, PostgreSQL usará el puerto 5432." -ForegroundColor Gray
    }
} else {
    Write-Host "    • Datos de PostgreSQL ya existentes en $PgDataDir ✅" -ForegroundColor Green
}

# 4. Install backend dependencies
Write-Host "==> [Paso 4/5] Instalando dependencias del backend Python..." -ForegroundColor Cyan
try {
    uv sync
    Write-Host "    • Dependencias de Python sincronizadas ✅" -ForegroundColor Green
} catch {
    Write-Warning "Hubo un error al ejecutar 'uv sync'. Verifica tu conexion o python."
}

# 5. Create Desktop Shortcut for Control Panel
Write-Host "==> [Paso 5/5] Creando acceso directo en el Escritorio..." -ForegroundColor Cyan
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Vitalcer Control Panel.lnk"
$TargetBat = Join-Path $RepoRoot "scripts\windows\run_control.bat"

try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $TargetBat
    $Shortcut.WorkingDirectory = $RepoRoot
    $Shortcut.Description = "Panel de Control de Servicios de Vitalcer"
    $Shortcut.Save()
    Write-Host "    • Acceso directo creado: $ShortcutPath ✅" -ForegroundColor Green
} catch {
    Write-Warning "No se pudo crear el acceso directo en el Escritorio."
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  Instalacion completada con exito!               " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Ya puedes hacer doble click en el acceso directo de tu Escritorio"
Write-Host "o ejecutar: scripts\windows\run_control.bat"
Write-Host ""
pause
