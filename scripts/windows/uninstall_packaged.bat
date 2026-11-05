@echo off
title Desinstalador de Vitalcer
cd /d "%~dp0"

echo ====================================================
echo  Iniciando Asistente de Desinstalacion de Vitalcer...
echo ====================================================

if exist "unins000.exe" (
    start "" "unins000.exe"
    exit /b 0
)

echo [ERROR] No se encontro el archivo desinstalador unins000.exe en esta carpeta.
pause
exit /b 1
