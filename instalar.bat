@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ================================================
echo   Instalador - Agente de Encuesta de Hogares
echo ================================================
echo.

REM --- 1. Verificar Node.js (lo necesita Claude Code) ---
where node >nul 2>nul
if errorlevel 1 (
    echo [1/4] No se encontro Node.js en esta computadora.
    echo        Se va a abrir la pagina de descarga en tu navegador.
    echo        Instalalo con las opciones por defecto del instalador,
    echo        y despues volve a hacer doble clic en este archivo,
    echo        instalar.bat, para continuar donde quedaste.
    echo.
    start https://nodejs.org
    if not defined ENCUESTA_HOGARES_NONINTERACTIVE pause
    exit /b 1
)
echo [1/4] Node.js encontrado: OK

REM --- 2. Verificar/instalar Claude Code ---
REM Version FIJADA a proposito, no "lo ultimo que haya hoy": el proyecto
REM se probo de punta a punta con esta version, y un instalador que trae
REM una version distinta segun el dia convierte cualquier cambio de
REM comportamiento de Claude Code en un "no me funciona" indiagnosticable
REM a distancia. Para actualizarla: probar el flujo completo con la
REM version nueva y recien entonces cambiar este numero (misma logica que
REM fijar el modelo en abrir_agente.bat).
where claude >nul 2>nul
if errorlevel 1 (
    echo [2/4] Instalando Claude Code, puede tardar un minuto...
    call npm install -g @anthropic-ai/claude-code@2.1.233
    if errorlevel 1 (
        echo.
        echo No se pudo instalar Claude Code. Revisa tu conexion a
        echo internet y volve a intentar.
        if not defined ENCUESTA_HOGARES_NONINTERACTIVE pause
        exit /b 1
    )
) else (
    echo [2/4] Claude Code ya estaba instalado: OK
)

REM --- 3. Detectar Python (Anaconda) e instalar dependencias del proyecto ---
REM Se prueba primero la ubicacion tipica de Anaconda, sin depender del
REM PATH: Windows trae un "python.exe" falso propio (el alias de Microsoft
REM Store) que aparece en el PATH aunque no haya ningun Python instalado
REM de verdad, asi que "where python" solo no alcanza para confiar en el.
set "PYEXE=C:\Users\%USERNAME%\anaconda3\python.exe"

if not exist "!PYEXE!" (
    set "PYEXE="
    for /f "delims=" %%v in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYEXE=%%v"

    if "!PYEXE!"=="" (
        echo.
        echo No se encontro una instalacion de Python/Anaconda utilizable.
        echo Instala Anaconda desde https://www.anaconda.com/download y
        echo volve a correr este instalador.
        if not defined ENCUESTA_HOGARES_NONINTERACTIVE pause
        exit /b 1
    )
)

echo [3/4] Instalando las dependencias de Python del proyecto...
"!PYEXE!" -m pip install -e ".[dev]" --quiet
if errorlevel 1 (
    echo.
    echo Hubo un problema instalando las dependencias de Python.
    if not defined ENCUESTA_HOGARES_NONINTERACTIVE pause
    exit /b 1
)

REM Guardar la ruta exacta de Python para que el agente la use directamente,
REM sin tener que volver a buscarla ni adivinar cada vez que corre un comando.
if not exist ".claude" mkdir ".claude"
> ".claude\python_path.txt" echo !PYEXE!

REM --- 4. Preparar el generador de PDF (descarga Chromium una sola vez) ---
echo [4/4] Preparando el generador de informes PDF, puede tardar unos minutos la primera vez...
"!PYEXE!" -m playwright install chromium
REM Sin este chequeo, si la descarga de Chromium fallaba (red, proxy,
REM antivirus) el instalador igual decia "Listo, ya esta todo instalado" y
REM el problema recien aparecia mucho despues, al generar el PDF en medio
REM de una corrida real.
if errorlevel 1 (
    echo.
    echo No se pudo preparar el generador de informes PDF. Revisa tu
    echo conexion a internet y volve a correr este instalador.
    if not defined ENCUESTA_HOGARES_NONINTERACTIVE pause
    exit /b 1
)

echo.
echo ================================================
echo   Listo. Ya esta todo instalado.
echo ================================================
echo.
REM Antes esto mandaba a abrir una terminal y escribir `claude`, que es
REM justo lo contrario a todo el diseno del proyecto (el usuario no
REM deberia ver nunca la terminal) y ademas contradecia al README, que
REM manda a abrir_agente.bat.
echo Para usar el agente, cerra esta ventana y hace doble clic en
echo el archivo "abrir_agente.bat", que esta en esta misma carpeta.
echo.
echo No hace falta escribir ningun comando: el agente te va a ir
echo preguntando todo con formularios que se abren en el navegador.
echo.
if not defined ENCUESTA_HOGARES_NONINTERACTIVE pause
