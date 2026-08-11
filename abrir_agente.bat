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

REM Minimiza esta terminal mientras se responde el formulario de arranque
REM (bienvenida con botones "Empezar" / "Salir"), para que lo primero que
REM se vea sea ese formulario en el navegador, no una consola vacia. Es
REM solo cosmetico: si falla, el arranque sigue igual.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0.claude\arranque\ventana.ps1" -Titulo "Agente - Encuesta de Hogares" -Accion Minimizar >nul 2>nul

set "ACCION="
for /f "delims=" %%A in ('run_python.bat arranque.py') do set "ACCION=%%A"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0.claude\arranque\ventana.ps1" -Titulo "Agente - Encuesta de Hogares" -Accion Restaurar >nul 2>nul

if /i not "%ACCION%"=="EMPEZAR" (
    exit /b 0
)

claude "Quiero hacer la encuesta de hogares"

echo.
echo La sesion de Claude Code termino.
pause
