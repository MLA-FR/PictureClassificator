@echo off
chcp 65001 >nul
echo ============================================
echo    Installation du Classeur de photos
echo ============================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] Python introuvable.
  echo Installe Python 3.12 depuis https://www.python.org/downloads/windows/
  echo en cochant "Add python.exe to PATH", puis relance ce fichier.
  echo.
  pause
  exit /b 1
)
if not exist .venv (
  echo Creation de l'environnement Python...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo.
echo Installation des composants (plusieurs minutes ; le moteur de visages
echo telecharge environ 200 Mo). Chaque composant est installe separement.
echo.
echo --- 1/3 : interface (pywebview)
pip install pywebview
echo --- 2/3 : moteur de visages (facenet-pytorch + torch)
pip install facenet-pytorch
echo --- 3/3 : photos iPhone (.heic)
pip install pillow-heif

echo.
echo ============================================
echo    Verification
echo ============================================
python -c "import webview, torch, facenet_pytorch; print('OK : tous les composants sont installes.')"
if errorlevel 1 (
  echo.
  echo [PROBLEME] Un composant n'a pas pu s'installer ^(voir les lignes rouges plus haut^).
  echo Cause frequente en entreprise : un proxy / pare-feu bloque les telechargements.
  echo Copie la ligne d'erreur et envoie-la pour diagnostic.
) else (
  echo.
  echo Installation terminee. Lance l'application avec  lancer.bat
  echo Au 1er lancement, le modele se telecharge ^(~110 Mo, une seule fois^).
)
echo.
pause
