import io
import base64
from PIL import Image
from datetime import datetime

DEBUG = True

def dbg(tag, payload=None):
    if not DEBUG:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[FACE_EXTRACT {ts}] {tag}")
    if payload is not None:
        print(payload)

# =========================
# FACE TEMPLATE PER STATE
# =========================
STATE_FACE_TEMPLATE = {
    "GENERAL": {
        # template aman (kiri-tengah)
        "x1": 0.04,
        "y1": 0.15,
        "x2": 0.35,
        "y2": 0.70
    },

    "MARYLAND": {
        "x1": 0.01,   # geser lebih ke kiri
        "y1": 0.20,   # atas kotak foto (sudah pas)
        "x2": 0.26,   # POTONG KANAN LAGI (hilangkan teks)
        "y2": 0.80    # bawah kotak foto
    },


    "NEW YORK": {
        "x1": 0.04,
        "y1": 0.20,
        "x2": 0.30,
        "y2": 0.60
    },

    "VIRGINIA": {
        "x1": 0.06,
        "y1": 0.17,
        "x2": 0.34,
        "y2": 0.65
    }
}

# =========================
# CORE FACE CROP
# =========================
def crop_face_by_state(image_rgb, state_name=None):
    img = Image.fromarray(image_rgb).convert("RGB")
    w, h = img.size

    key = (state_name or "").upper()
    tpl = STATE_FACE_TEMPLATE.get(key)

    if not tpl:
        dbg("STATE_NOT_FOUND_USING_GENERAL", state_name)
        tpl = STATE_FACE_TEMPLATE["GENERAL"]

    box = (
        int(w * tpl["x1"]),
        int(h * tpl["y1"]),
        int(w * tpl["x2"]),
        int(h * tpl["y2"]),
    )

    dbg("CROP_BOX", {
        "state": key or "NONE",
        "box": box
    })

    return img.crop(box)

# =========================
# IMAGE TO BASE64
# =========================
def face_to_base64(face_img: Image.Image):
    buf = io.BytesIO()
    face_img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
