#!/bin/bash
cd "$(dirname "$0")"
echo "============================================"
echo "   Installation du Classeur de photos (macOS)"
echo "============================================"
echo
if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  echo "[ERREUR] Python 3 introuvable."
  echo "Installe Python 3.12 depuis https://www.python.org/downloads/macos/ puis relance ce fichier."
  read -n 1 -s -r -p "Appuie sur une touche pour fermer..."
  exit 1
fi
if [ ! -d ".venv" ]; then
  echo "Creation de l'environnement Python..."
  "$PY" -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
echo
echo "Installation des composants (plusieurs minutes ; le moteur de visages telecharge ~200 Mo)..."
echo
echo "--- 1/2 : interface (pywebview)"
pip install pywebview
echo "--- 2/2 : moteur de visages (facenet-pytorch + torch)"
pip install facenet-pytorch "Pillow<10.3.0"
echo
echo "============================================"
echo "   Verification"
echo "============================================"
if python -c "import webview, torch, facenet_pytorch; print('OK : tous les composants sont installes.')"; then
  echo
  echo "Installation terminee. Lance l'application avec  lancer.command"
  echo "Au 1er lancement, le modele se telecharge (~110 Mo, une seule fois)."
else
  echo
  echo "[PROBLEME] Un composant n'a pas pu s'installer (voir les messages plus haut)."
  echo "Si la fenetre n'apparait pas ensuite, essaie :  pip install pyobjc"
fi
echo
read -n 1 -s -r -p "Appuie sur une touche pour fermer..."
