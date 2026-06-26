import os, threading, base64
from pathlib import Path

import webview

from engine import store, faces, classify


def _safe(s):
    return "".join(c for c in s if c.isalnum() or c in "-_") or "p"


def _thumb_uri(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


class Api:
    def __init__(self):
        self.gallery = store.load_gallery()
        self.settings = store.load_settings()
        self.plan = None
        self.group_names = {}
        self.progress = {}
        self.cancel = {"flag": False}
        self._pending = {}          # chemin -> (bgr, dets) pour l'enrolement

    def _win(self):
        return webview.windows[0]

    # ---------- selection fichiers ----------
    def pick_folder(self):
        r = self._win().create_file_dialog(webview.FOLDER_DIALOG)
        return r[0] if r else None

    def pick_images(self):
        ft = ("Images (*.jpg;*.jpeg;*.png;*.webp;*.tif;*.tiff;*.bmp;*.heic;*.heif)",)
        r = self._win().create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=True, file_types=ft)
        return list(r) if r else []

    # ---------- parametres ----------
    def get_settings(self):
        return self.settings

    def set_settings(self, s):
        self.settings.update(s or {})
        store.save_settings(self.settings)
        return self.settings

    # ---------- personnes ----------
    def get_people(self):
        return [{"name": n, "count": len(d.get("refs", [])), "thumb": _thumb_uri(d.get("thumb"))}
                for n, d in self.gallery.items()]

    def remove_person(self, name):
        self.gallery.pop(name, None)
        store.save_gallery(self.gallery)
        return self.get_people()

    def detect_in_files(self, paths):
        """Detecte les visages dans les photos de reference choisies."""
        out = []
        for p in paths:
            try:
                bgr, dets = faces.detect(p, self.settings.get("gpu", False))
                self._pending[p] = (bgr, dets)
                out.append({
                    "path": p, "n": len(dets),
                    "faces": [{"idx": i, "crop": faces.crop_b64(bgr, d["bbox"])}
                              for i, d in enumerate(dets)],
                })
            except Exception as e:
                out.append({"path": p, "n": 0, "faces": [], "error": str(e)})
        return out

    def enroll(self, name, selections):
        """selections = [{path, idx}] : enregistre les empreintes choisies."""
        name = (name or "").strip()
        if not name:
            return {"error": "Le prénom est vide."}
        entry = self.gallery.get(name, {"refs": [], "thumb": None})
        added = 0
        for sel in (selections or []):
            data = self._pending.get(sel.get("path"))
            idx = sel.get("idx", -1)
            if not data:
                continue
            bgr, dets = data
            if idx < 0 or idx >= len(dets):
                continue
            entry["refs"].append([float(x) for x in dets[idx]["embedding"]])
            added += 1
            if not entry["thumb"]:
                tp = store.data_dir() / "thumbs" / f"{_safe(name)}.jpg"
                faces.save_thumb(bgr, dets[idx]["bbox"], tp)
                entry["thumb"] = str(tp)
        if added == 0:
            return {"error": "Aucun visage sélectionné."}
        self.gallery[name] = entry
        store.save_gallery(self.gallery)
        self._pending.clear()
        return {"ok": True, "people": self.get_people()}

    # ---------- analyse / execution ----------
    def count_images(self, root):
        try:
            return {"count": len(classify.list_images(root, self.settings.get("heic", True)))}
        except Exception as e:
            return {"error": str(e)}

    def start_analyze(self, root):
        self.cancel = {"flag": False}
        self.progress = {"phase": "analyze", "done": 0, "total": 0, "done_flag": False}

        def job():
            try:
                plan, counts, errors, groups = classify.analyze(
                    root, self.gallery, self.settings, self.progress, self.cancel)
                self.plan = plan
                self.group_names = groups
            except Exception as e:
                self.progress["error"] = str(e)
            finally:
                self.progress["done_flag"] = True

        threading.Thread(target=job, daemon=True).start()
        return {"started": True}

    def start_execute(self, out_dir):
        if not self.plan:
            return {"error": "Aucun plan : lance d'abord l'aperçu."}
        self.cancel = {"flag": False}
        self.progress = {"phase": "execute", "done": 0,
                         "total": len(self.plan), "done_flag": False}

        def job():
            try:
                classify.execute(self.plan, out_dir, self.settings,
                                 self.progress, self.cancel, self.group_names)
            except Exception as e:
                self.progress["error"] = str(e)
            finally:
                self.progress["done_flag"] = True

        threading.Thread(target=job, daemon=True).start()
        return {"started": True, "out": out_dir}

    def get_progress(self):
        return self.progress

    def cancel_job(self):
        self.cancel["flag"] = True
        return {"ok": True}


def main():
    base = Path(__file__).parent
    api = Api()
    webview.create_window(
        "Classeur de photos par visage",
        str(base / "ui" / "index.html"),
        js_api=api, width=1120, height=780, min_size=(920, 640),
    )
    webview.start()


if __name__ == "__main__":
    main()
