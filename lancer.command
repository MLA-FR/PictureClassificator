#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null
if ! python -c "import webview" >/dev/null 2>&1; then
  echo "Les composants ne sont pas installes. Lance d'abord  installer.command"
  read -n 1 -s -r -p "Appuie sur une touche pour fermer..."
  exit 1
fi
python app.py
