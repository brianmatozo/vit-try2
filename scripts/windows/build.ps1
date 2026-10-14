# PowerShell Build Script for Vitalcer Static SPAs
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Set-Location $RepoRoot

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Compilando Aplicaciones Estaticas de Vitalcer... " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

Write-Host "==> [1/4] Exportando esquema OpenAPI..." -ForegroundColor Yellow
uv run python scripts/api_export.py

Write-Host "==> [2/4] Regenerando cliente @vitalcer/api..." -ForegroundColor Yellow
pnpm --filter @vitalcer/api generate

Write-Host "==> [3/4] Compilando Admin y POS SPAs (SvelteKit)..." -ForegroundColor Yellow
pnpm -r --filter "./apps/*" build

Write-Host "==> [4/4] Pre-comprimiendo activos con Brotli y Gzip (Nivel 11)..." -ForegroundColor Yellow
node scripts/compress_static.mjs

Write-Host "Compilacion completada con exito! ✅" -ForegroundColor Green
