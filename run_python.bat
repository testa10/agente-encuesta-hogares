@echo off
REM Envoltorio fijo: el agente siempre invoca "run_python.bat", nunca la
REM ruta real de Python (que cambia en cada computadora). Lee la ruta
REM detectada por instalar.bat en .claude\python_path.txt y le reenvia
REM todos los argumentos. Esto tambien permite que la regla de permisos
REM en .claude\settings.json sea la misma para cualquier usuario.
setlocal
set "AQUI=%~dp0"
set /p PYEXE=<"%AQUI%.claude\python_path.txt"
"%PYEXE%" %*
