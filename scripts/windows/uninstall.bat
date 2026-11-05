@echo off
setlocal enabledelayedexpansion

title Desinstalador de Vitalcer (Desarrollo)
cd /d "%~dp0..\.."

echo ====================================================
echo  Iniciando Desinstalacion y Limpieza...
echo ====================================================

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Hubo un problema durante la desinstalacion.
    pause
    exit /b %ERRORLEVEL%
)

exit /b 0
