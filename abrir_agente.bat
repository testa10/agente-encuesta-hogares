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

REM Se probo -p/--print acá (corre el pedido y termina el proceso solo,
REM en vez de quedarse en una sesion interactiva esperando mas mensajes
REM para siempre) para que la consola se cierre sola al terminar o al
REM salir antes. Revertido: en una prueba real, con -p el flujo se
REM cortaba a mitad de camino y volvia a mostrar el formulario de
REM bienvenida desde cero después de contestar el del año - -p no
REM sostiene bien una conversacion larga con formularios que bloquean
REM varios minutos esperando al usuario. El problema original (la
REM consola queda viva de fondo sin cerrarse sola) sigue sin resolver;
REM antes de volver a intentarlo, confirmar con la documentacion de
REM Claude Code si hay una forma de cerrar el proceso al final de un
REM turno largo sin cambiar el modo de ejecucion.
claude "Quiero hacer la encuesta de hogares"

echo.
echo La sesion de Claude Code termino.
pause
