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
    pause
    exit /b 1
)
echo [1/4] Node.js encontrado: OK

REM --- 2. Verificar/instalar Claude Code ---
where claude >nul 2>nul
if errorlevel 1 (
    echo [2/4] Instalando Claude Code, puede tardar un minuto...
    call npm install -g @anthropic-ai/claude-code
    if errorlevel 1 (
        echo.
        echo No se pudo instalar Claude Code. Revisa tu conexion a
        echo internet y volve a intentar.
        pause
        exit /b 1
    )
) else (
    echo [2/4] Claude Code ya estaba instalado: OK
)

REM --- 3. Detectar Python (Anaconda) e instalar dependencias del proyecto ---
where python >nul 2>nul
if errorlevel 1 (
    set "PYEXE=C:\Users\%USERNAME%\anaconda3\python.exe"
) else (
    set "PYEXE=python"
)

if not exist "!PYEXE!" (
    if not "!PYEXE!"=="python" (
        echo.
        echo No se encontro una instalacion de Python/Anaconda en la ruta
        echo esperada: !PYEXE! - Instala Anaconda desde
        echo https://www.anaconda.com/download y volve a correr este
        echo instalador.
        pause
        exit /b 1
    )
)

echo [3/4] Instalando las dependencias de Python del proyecto...
"!PYEXE!" -m pip install -e ".[dev]" --quiet
if errorlevel 1 (
    echo.
    echo Hubo un problema instalando las dependencias de Python.
    pause
    exit /b 1
)

REM --- 4. Preparar el generador de PDF (descarga Chromium una sola vez) ---
echo [4/4] Preparando el generador de informes PDF, puede tardar unos minutos la primera vez...
"!PYEXE!" -m playwright install chromium

echo.
echo ================================================
echo   Listo! Ya esta todo instalado.
echo ================================================
echo.
echo Para usar el agente:
echo   1. Abri una terminal en esta carpeta, o segui usando esta
echo      misma ventana.
echo   2. Escribi: claude
echo   3. Pedile el analisis que necesites, en tus palabras.
echo.
pause
