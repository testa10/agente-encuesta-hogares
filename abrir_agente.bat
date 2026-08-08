@echo off
cd /d "%~dp0"
title Agente - Encuesta de Hogares

where claude >nul 2>nul
if errorlevel 1 (
    echo No se encontro Claude Code en esta computadora.
    echo Corre primero instalar.bat, que esta en esta misma carpeta.
    pause
    exit /b 1
)

claude

echo.
echo La sesion de Claude Code termino.
pause
