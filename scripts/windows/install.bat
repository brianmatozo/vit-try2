@echo off
setlocal enabledelayedexpansion

title Instalador de Vitalcer (Windows)
cd /d "%~dp0..\.."

echo ====================================================
echo  Iniciando Asistente de Instalacion de Vitalcer...
echo ====================================================

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Hubo un problema durante la instalacion.
    pause
    exit /b %ERRORLEVEL%
)

exit /b 0
