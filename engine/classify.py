import os, shutil, unicodedata, hashlib
from pathlib import Path
import numpy as np

from . import faces

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
HEIC_EXT = {".heic", ".heif"}


def list_images(root, heic=True):
    exts = set(IMG_EXT) | (HEIC_EXT if heic else set())
    out = []
    for dp, _, files in os.walk(root):
        for fn in files:
            if Path(fn).suffix.lower() in exts:
                out.append(os.path.join(dp, fn))
    return out


def best_match(emb, gallery, seuil):
    """Meilleure correspondance (cosinus = produit scalaire d'empreintes normalisees)."""
    best_name, best_sim = None, -1.0
    for name, data in gallery.items():
        for ref in data.get("refs", []):
            sim = float(np.dot(emb, np.asarray(ref, dtype=np.float32)))
            if sim > best_sim:
                best_sim, best_name = sim, name
    return (best_name, best_sim) if best_sim >= seuil else (None, best_sim)


def _sort_key(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def sanitize(name):
    for c in '/\\:*?"<>|':
        name = name.replace(c, "")
    return name.strip()


def folder_for(names, settings):
    """Nom du dossier pour l'ensemble des personnes connues reconnues."""
    uniq = sorted({n for n in names}, key=_sort_key)
    uniq = [sanitize(n) for n in uniq if sanitize(n)]
    if not uniq:
        return None
    if len(uniq) == 1:
        return uniq[0]
    joined = "_".join(uniq)
    if len(uniq) > int(settings.get("max_noms", 6)) or len(joined) > 120:
        h = hashlib.md5(joined.encode("utf-8")).hexdigest()[:8]
        return f"Groupe_{h}"
    return joined


def analyze(root, gallery, settings, progress, cancel):
    """Construit le plan (src -> dossier) sans rien copier. Renseigne `progress`."""
    imgs = list_images(root, settings.get("heic", True))
    progress["total"] = len(imgs)
    progress["done"] = 0
    plan, counts, errors, group_names = [], {}, [], {}

    for i, path in enumerate(imgs):
        if cancel.get("flag"):
            break
        progress["done"] = i + 1
        progress["current"] = os.path.basename(path)
        try:
            _bgr, dets = faces.detect(path, settings.get("gpu", False))
        except Exception as e:
            errors.append((path, str(e)))
            folder = settings["dossier_erreurs"]
            plan.append((path, folder))
            counts[folder] = counts.get(folder, 0) + 1
            continue

        if not dets:
            folder = settings["dossier_sans_visage"]
        else:
            names = []
            for d in dets:
                n, _ = best_match(d["embedding"], gallery, settings["seuil"])
                if n:
                    names.append(n)
            if not names:
                folder = settings["dossier_inconnus"]
            else:
                folder = folder_for(names, settings)
                if folder and folder.startswith("Groupe_"):
                    group_names[folder] = sorted(set(names), key=_sort_key)

        plan.append((path, folder))
        counts[folder] = counts.get(folder, 0) + 1

    progress["counts"] = counts
    progress["errors"] = len(errors)
    progress["groups"] = group_names
    return plan, counts, errors, group_names


def _unique(p):
    p = Path(p)
    if not p.exists():
        return str(p)
    i = 1
    while True:
        cand = p.parent / f"{p.stem}_{i}{p.suffix}"
        if not cand.exists():
            return str(cand)
        i += 1


def execute(plan, out_dir, settings, progress, cancel, group_names=None):
    mode = settings.get("mode", "copier")
    out = Path(out_dir)
    progress["total"] = len(plan)
    progress["done"] = 0
    done = 0
    written_groups = set()

    for i, (src, folder) in enumerate(plan):
        if cancel.get("flag"):
            break
        progress["done"] = i + 1
        dst_dir = out / folder
        dst_dir.mkdir(parents=True, exist_ok=True)
        # Pour les dossiers "Groupe_xxx", deposer un fichier listant les prenoms
        if group_names and folder in group_names and folder not in written_groups:
            try:
                (dst_dir / "_personnes.txt").write_text(
                    "\n".join(group_names[folder]), encoding="utf-8")
            except Exception:
                pass
            written_groups.add(folder)
        dst = _unique(dst_dir / Path(src).name)
        try:
            if mode == "deplacer":
                shutil.move(src, dst)
            else:
                shutil.copy2(src, dst)
            done += 1
        except Exception:
            pass

    progress["moved"] = done
    return done
