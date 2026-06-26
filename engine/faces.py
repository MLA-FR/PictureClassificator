import io, base64
import numpy as np
from PIL import Image

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

_MTCNN = None
_RESNET = None
_DEVICE = "cpu"


def init_model(gpu=False):
    """Charge MTCNN (detection) + InceptionResnetV1/VGGFace2 (empreintes), une seule fois."""
    global _MTCNN, _RESNET, _DEVICE
    if _RESNET is not None:
        return
    import torch
    from facenet_pytorch import MTCNN, InceptionResnetV1
    if gpu and torch.cuda.is_available():
        _DEVICE = "cuda"
    elif gpu and getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        _DEVICE = "mps"
    else:
        _DEVICE = "cpu"
    _MTCNN = MTCNN(keep_all=True, device=_DEVICE)
    _RESNET = InceptionResnetV1(pretrained="vggface2").eval().to(_DEVICE)


def load_rgb(path):
    return Image.open(path).convert("RGB")


def detect(path, gpu=False):
    """Retourne (image_rgb(np), [ {embedding(np 512 normalisee), bbox[x1,y1,x2,y2]} ])."""
    init_model(gpu)
    import torch
    from facenet_pytorch import extract_face
    img = load_rgb(path)
    arr = np.array(img)
    boxes, probs = _MTCNN.detect(img)
    out = []
    if boxes is None:
        return arr, out

    crops, kept = [], []
    for box, p in zip(boxes, probs):
        if p is None or p < 0.90:
            continue
        try:
            face = extract_face(img, box, image_size=160)   # (3,160,160), ~[0,255]
            face = (face - 127.5) / 128.0                   # normalisation FaceNet
        except Exception:
            continue
        crops.append(face)
        kept.append(box)
    if not crops:
        return arr, out

    with torch.no_grad():
        embs = _RESNET(torch.stack(crops).to(_DEVICE)).cpu().numpy()

    for box, e in zip(kept, embs):
        n = float(np.linalg.norm(e))
        e = e / n if n > 0 else e
        x1, y1, x2, y2 = [int(round(float(v))) for v in box]
        out.append({"embedding": e.astype(np.float32), "bbox": [x1, y1, x2, y2]})
    return arr, out


def _crop(rgb, bbox, size=160):
    x1, y1, x2, y2 = bbox
    h, w = rgb.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return None
    im = Image.fromarray(rgb[y1:y2, x1:x2])
    im.thumbnail((size, size))
    return im


def crop_b64(rgb, bbox, size=160):
    im = _crop(rgb, bbox, size)
    if im is None:
        return None
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def save_thumb(rgb, bbox, dest, size=160):
    im = _crop(rgb, bbox, size)
    if im is not None:
        im.save(dest, format="JPEG", quality=85)
