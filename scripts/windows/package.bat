@echo off
setlocal enabledelayedexpansion

title Compilador de Instalador Vitalcer (Windows)
cd /d "%~dp0..\.."

echo ====================================================
echo  Iniciando Empaquetado y Creacion del Instalador...
echo ====================================================

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0package.ps1"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Hubo un problema durante el empaquetado del instalador.
    pause
    exit /b %ERRORLEVEL%
)

pause
exit /b 0
