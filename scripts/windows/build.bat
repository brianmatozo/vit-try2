@echo off
setlocal enabledelayedexpansion

title Vitalcer Build Pipeline
cd /d "%~dp0..\.."

echo ====================================================
echo  Compilando Aplicaciones Estaticas de Vitalcer...
echo ====================================================

echo [1/4] Exportando esquema OpenAPI...
uv run python scripts\api_export.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Fallo la exportacion de OpenAPI.
    exit /b %ERRORLEVEL%
)

echo [2/4] Regenerando cliente @vitalcer/api...
call pnpm --filter @vitalcer/api generate
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Fallo la generacion de codigo API.
    exit /b %ERRORLEVEL%
)

echo [3/4] Compilando Admin y POS SPAs (SvelteKit)...
call pnpm -r --filter "./apps/*" build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Fallo la compilacion de las aplicaciones.
    exit /b %ERRORLEVEL%
)

echo [4/4] Pre-comprimiendo activos con Brotli y Gzip (Nivel 11)...
node scripts\compress_static.mjs
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Fallo la pre-compresion estatica.
    exit /b %ERRORLEVEL%
)

echo ====================================================
echo  Compilacion finalizada exitosamente! ✅
echo ====================================================
