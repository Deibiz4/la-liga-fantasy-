@echo off
title LaLiga Fantasy Bot Manager
chcp 65001 > nul
cd /d "%~dp0"

:: Set unbuffered python output
set PYTHONUNBUFFERED=1

echo ==============================================================================
echo                      ⚽  LALIGA FANTASY BOT - CONTROL PANEL  ⚽
echo ==============================================================================
echo.

:: Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python no está instalado o no se encuentra en el PATH del sistema.
    echo Por favor, instala Python 3.11+ desde https://www.python.org/ y vuelve a intentarlo.
    echo.
    pause
    exit /b 1
)

echo [OK] Python detectado en el sistema.
echo.
echo Selecciona la opción que deseas ejecutar:
echo.
echo   [1]  🚀 Iniciar Bot de Telegram (Daemon + Notificaciones + Autopilot)
echo   [2]  🌐 Iniciar Panel Web de Monitorización (Mission Control)
echo   [3]  📊 Ver Estadísticas de Usuarios de Telegram
echo   [4]  🤖 Ejecutar Auditoría / Agente Autónomo (Revisión de alineación y mercado)
echo   [5]  🔑 Iniciar Sesión / Renovar Token de LaLiga Fantasy
echo   [6]  ⚡ Escanear Clausulazos y Robos a Rivales (Rival Clause Flips)
echo   [7]  💻 Abrir Terminal / Consola de Comandos de Fantasybot
echo   [0]  ❌ Salir
echo.
echo ==============================================================================
set /p OPTION="Elige una opción [1-7] (por defecto 1): "

if "%OPTION%"=="" set OPTION=1
if "%OPTION%"=="1" goto start_telegram
if "%OPTION%"=="2" goto start_watch
if "%OPTION%"=="3" goto show_stats
if "%OPTION%"=="4" goto run_agent
if "%OPTION%"=="5" goto run_login
if "%OPTION%"=="6" goto run_clausulas
if "%OPTION%"=="7" goto open_cli
if "%OPTION%"=="0" goto exit_app

echo Opción no válida. Iniciando Bot de Telegram por defecto...
timeout /t 2 > nul
goto start_telegram

:start_telegram
cls
echo ==============================================================================
echo                      🚀  INICIANDO BOT DE TELEGRAM  🚀
echo ==============================================================================
echo.
echo Conectando con Telegram y arrancando motor de notificaciones...
echo Presiona Ctrl + C en cualquier momento para detener el bot.
echo.
python -u -m fantasybot telegram
echo.
echo El bot se ha detenido.
pause
goto exit_app

:start_watch
cls
echo ==============================================================================
echo                 🌐  PANEL DE CONTROL WEB (MISSION CONTROL)  🌐
echo ==============================================================================
echo.
echo Abriendo Mission Control en el navegador (http://127.0.0.1:9137)...
echo Presiona Ctrl + C en cualquier momento para detener el servidor web.
echo.
python -u -m fantasybot watch
pause
goto exit_app

:show_stats
cls
echo ==============================================================================
echo                  📊  ESTADÍSTICAS DE USUARIOS REGISTRADOS  📊
echo ==============================================================================
echo.
python -u -m fantasybot stats
echo.
pause
goto exit_app

:run_agent
cls
echo ==============================================================================
echo                  🤖  AUDITORÍA Y REVISIÓN DEL AGENTE  🤖
echo ==============================================================================
echo.
python -u -m fantasybot agent
echo.
pause
goto exit_app

:run_login
cls
echo ==============================================================================
echo                🔑  LOGIN EN LALIGA FANTASY (OAUTH2)  🔑
echo ==============================================================================
echo.
python -u -m fantasybot login
echo.
pause
goto exit_app

:run_clausulas
cls
echo ==============================================================================
echo           ⚡  BUSCADOR DE CLAUSULAZOS Y ROBOS A RIVALES  ⚡
echo ==============================================================================
echo.
python -u -m fantasybot clausulas
echo.
pause
goto exit_app

:open_cli
cls
echo ==============================================================================
echo                💻  CONSOLA INTERACTIVA DE FANTASYBOT  💻
echo ==============================================================================
echo.
echo Ejemplos de comandos disponibles:
echo   - python -m fantasybot clausulas
echo   - python -m fantasybot me
echo   - python -m fantasybot team
echo   - python -m fantasybot market
echo   - python -m fantasybot rivals
echo   - python -m fantasybot stats
echo.
cmd /k

:exit_app
exit /b 0
