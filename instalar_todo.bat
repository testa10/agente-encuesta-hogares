@echo off
setlocal enabledelayedexpansion
title Agente de Encuesta de Hogares - Instalacion completa

echo ================================================
echo   Agente de Encuesta de Hogares
echo   Descarga e instalacion completa
echo ================================================
echo.
echo Este script va a:
echo   1. Descargar el proyecto (si todavia no esta en tu computadora).
echo   2. Instalar lo que haga falta (Claude Code, dependencias de Python).
echo   3. Abrir el agente.
echo.
echo No modifica nada fuera de tu carpeta de Documentos.
echo.

set "DESTINO=%USERPROFILE%\Documents\agente-encuesta-hogares"

if exist "%DESTINO%\abrir_agente.bat" (
    echo Ya existe una instalacion en:
    echo   %DESTINO%
    echo Se va a usar esa carpeta tal cual esta, sin descargar de nuevo.
    echo.
) else (
    echo Descargando el proyecto en:
    echo   %DESTINO%
    echo Esto puede tardar un minuto, segun tu conexion...
    echo.

    if not exist "%USERPROFILE%\Documents" mkdir "%USERPROFILE%\Documents"
    if not exist "%DESTINO%" mkdir "%DESTINO%"

    set "ZIP=%TEMP%\agente-encuesta-hogares_descarga.zip"
    set "EXTRAIDO=%TEMP%\agente-encuesta-hogares_extraido"

    if exist "!EXTRAIDO!" rmdir /s /q "!EXTRAIDO!" >nul 2>nul

    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
         $ErrorActionPreference = 'Stop'; ^
         Invoke-WebRequest -Uri 'https://github.com/testa10/agente-encuesta-hogares/archive/refs/heads/main.zip' -OutFile '!ZIP!' -UseBasicParsing; ^
         Expand-Archive -Path '!ZIP!' -DestinationPath '!EXTRAIDO!' -Force; ^
         Copy-Item -Path (Join-Path '!EXTRAIDO!' 'agente-encuesta-hogares-main\*') -Destination '!DESTINO!' -Recurse -Force"

    if errorlevel 1 (
        echo.
        echo No se pudo descargar el proyecto. Revisa tu conexion a internet
        echo y volve a hacer doble clic en este archivo para intentar de nuevo.
        echo.
        pause
        exit /b 1
    )

    del /q "!ZIP!" >nul 2>nul
    rmdir /s /q "!EXTRAIDO!" >nul 2>nul

    if not exist "%DESTINO%\abrir_agente.bat" (
        echo.
        echo La descarga no se completo correctamente. Volve a hacer doble
        echo clic en este archivo para intentar de nuevo.
        echo.
        pause
        exit /b 1
    )

    echo Proyecto descargado.
    echo.
)

cd /d "%DESTINO%"

echo ================================================
echo   Verificando/instalando los programas necesarios
echo ================================================
echo.
call instalar.bat
if errorlevel 1 (
    echo.
    echo No se pudo terminar de instalar todo lo necesario - ver el mensaje
    echo de arriba. Una vez resuelto, volve a hacer doble clic en este mismo
    echo archivo (instalar_todo.bat) para continuar donde quedaste.
    echo.
    exit /b 1
)

echo.
echo ================================================
echo   Abriendo el agente
echo ================================================
echo.
call abrir_agente.bat
