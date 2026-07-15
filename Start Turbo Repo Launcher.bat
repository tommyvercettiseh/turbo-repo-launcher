@echo off
setlocal
cd /d "%~dp0"

title Turbo Repo Launcher

echo.
echo ========================================
echo   Turbo Repo Launcher
echo ========================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher is niet gevonden.
  echo Installeer Python 3.10 of nieuwer en vink Add Python to PATH aan.
  pause
  exit /b 1
)

if not exist .venv (
  echo Virtuele omgeving maken...
  py -m venv .venv
  if errorlevel 1 goto :error
)

call .venv\Scripts\activate

echo Dependencies controleren...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
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
