@echo off
setlocal enabledelayedexpansion

title Vitalcer Store Server (Consola)
cd /d "%~dp0..\.."

echo ====================================================
echo  Vitalcer Single-Store Server (Windows CLI)
echo ====================================================

where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    uv run python scripts\windows\service_manager.py --start-all
    exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python scripts\windows\service_manager.py --start-all
    exit /b %ERRORLEVEL%
)

echo [ERROR] No se encontro uv ni python en PATH.
pause
exit /b 1
