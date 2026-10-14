@echo off
setlocal enabledelayedexpansion

title Vitalcer Control Panel Launcher
cd /d "%~dp0..\.."

echo ====================================================
echo  Iniciando Panel de Control de Vitalcer...
echo ====================================================

:: Check if uv or python is available
where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    start "" uv run pythonw scripts\windows\vitalcer_control.py
    exit /b 0
)

where pythonw >nul 2>nul
if %ERRORLEVEL% equ 0 (
    start "" pythonw scripts\windows\vitalcer_control.py
    exit /b 0
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python scripts\windows\vitalcer_control.py
    exit /b 0
)

echo [ERROR] No se encontro Python ni uv instalado en el sistema.
echo Por favor ejecuta primero scripts\windows\install.bat
pause
exit /b 1
