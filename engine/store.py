import json, os, hashlib
from pathlib import Path

DEFAULT_SETTINGS = {
    "seuil": 0.5,
    "mode": "copier",                # "copier" ou "deplacer"
    "dossier_inconnus": "Inconnus",
    "dossier_sans_visage": "Sans visage",
    "dossier_erreurs": "Erreurs",
    "heic": True,
    "gpu": False,
    "max_noms": 6,
}


def data_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
    d = Path(base) / "ClasseurPhotos"
    (d / "thumbs").mkdir(parents=True, exist_ok=True)
    return d


def _p(name):
    return data_dir() / name


def load_gallery():
    p = _p("galerie.json")
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_gallery(g):
    _p("galerie.json").write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")


def load_settings():
    s = dict(DEFAULT_SETTINGS)
    p = _p("parametres.json")
    if p.exists():
        try:
            s.update(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return s


def save_settings(s):
    _p("parametres.json").write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")


def file_hash(path, chunk=1 << 16):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()
