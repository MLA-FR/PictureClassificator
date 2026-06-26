@echo off
chcp 65001 >nul
call .venv\Scripts\activate.bat
pip install pyinstaller
pyinstaller --noconfirm --windowed --name ClasseurPhotos --add-data "ui;ui" app.py
echo.
echo Executable dans dist\ClasseurPhotos\  (le modele se telecharge toujours au 1er lancement)
pause
