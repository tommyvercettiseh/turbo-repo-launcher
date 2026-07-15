@echo off
setlocal
cd /d "%~dp0"

title Turbo Repo Hub

set "WINDOWS_APPS=%LOCALAPPDATA%\Microsoft\WindowsApps"
set "PATH=%PATH%;%WINDOWS_APPS%"
set "WINGET_EXE=%WINDOWS_APPS%\winget.exe"
set "PYTHON_CMD="

echo.
echo ========================================
echo   Turbo Repo Hub
echo ========================================
echo.

where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py"

if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
  echo Python 3.10 of nieuwer is niet gevonden.
  echo.
  if exist "%WINGET_EXE%" (
    echo Python installeren via WinGet...
    "%WINGET_EXE%" install --id Python.Python.3.13 -e --source winget
  ) else (
    echo WinGet is niet gevonden op:
    echo   %WINGET_EXE%
    echo.
    echo Installeer of herstel Microsoft App Installer.
  )
  pause
  exit /b 1
)

echo Python gevonden via: %PYTHON_CMD%

if exist "%WINGET_EXE%" (
  for /f "delims=" %%V in ('"%WINGET_EXE%" --version 2^>nul') do echo WinGet gevonden: %%V
)

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

echo Turbo Repo Hub openen op http://127.0.0.1:8787
start "" http://127.0.0.1:8787
python -m uvicorn app.main:app --host 127.0.0.1 --port 8787
exit /b 0

:error
echo.
echo Starten is mislukt. Bekijk de melding hierboven.
pause
exit /b 1
