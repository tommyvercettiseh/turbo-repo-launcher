@echo off
setlocal
cd /d "%~dp0"

title Turbo Repo Launcher

echo.
echo ========================================
echo   Turbo Repo Launcher
echo ========================================
echo.

set "PYTHON_CMD="

where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py"

if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
  echo Python 3.10 of nieuwer is niet gevonden.
  echo.
  echo Installeer Python met:
  echo   winget install --id Python.Python.3.13 -e
  echo.
  echo Sluit daarna PowerShell en Visual Studio Code volledig af,
  echo open ze opnieuw en start dit bestand nogmaals.
  pause
  exit /b 1
)

echo Python gevonden via: %PYTHON_CMD%

if not exist .venv (
  echo Virtuele omgeving maken...
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto :error
)

call .venv\Scripts\activate.bat
if errorlevel 1 goto :error

echo Dependencies controleren...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Launcher openen op http://127.0.0.1:8787
start "" http://127.0.0.1:8787
python -m uvicorn app.main:app --host 127.0.0.1 --port 8787
exit /b 0

:error
echo.
echo Starten is mislukt. Bekijk de melding hierboven.
pause
exit /b 1
