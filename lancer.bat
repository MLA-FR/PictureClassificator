@echo off
chcp 65001 >nul
call .venv\Scripts\activate.bat
python -c "import webview" 2>nul
if errorlevel 1 (
  echo Les composants ne sont pas installes. Lance d'abord  installer.bat
  echo.
  pause
  exit /b 1
)
python app.py
if errorlevel 1 pause
