import re
import pytesseract
import numpy as np
from datetime import datetime
from processors.face_extractor import crop_face_by_state, face_to_base64

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# =========================
# SIMPLE DEBUG HELPER
# =========================
DEBUG = True

def dbg(tag, payload=None):
    if not DEBUG:
        return

    def to_python(obj):
        try:
            import numpy as np
            if isinstance(obj, np.generic):
                return obj.item()
            if isinstance(obj, np.ndarray):
                return obj.tolist()
        except Exception:
            pass
        return obj

    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[DL_DEBUG {ts}] {tag}")

    if payload is not None:
        if isinstance(payload, (list, dict)):
            import json
            safe = json.loads(json.dumps(payload, default=to_python))
            print(json.dumps(safe, indent=2))
        else:
            print(to_python(payload))

# =========================
# OCR
# =========================
def read_text(img, reader):
    try:
        res = reader.readtext(img, detail=0, paragraph=False)
        dbg("OCR_EASYOCR_RESULT", res)
        if res:
            return " ".join(res).strip()
    except Exception as e:
        dbg("OCR_EASYOCR_ERROR", str(e))

    txt = pytesseract.image_to_string(
        img, config="--oem 1 --psm 7"
    ).strip()

    dbg("OCR_TESSERACT_RESULT", txt)
    return txt

# =========================
# CLEANERS
# =========================
def clean_license_number(txt):
    cleaned = re.sub(r"[^A-Z0-9]", "", txt.upper()).replace("O", "0")
    dbg("CLEAN_LICENSE", {"raw": txt, "clean": cleaned})
    return cleaned

def clean_date(txt):
    m = re.search(r"(\d{2})\D(\d{2})\D(\d{4})", txt)
    if m:
        d, m_, y = m.groups()
        date = f"{d}/{m_}/{y}"
        dbg("CLEAN_DATE_OK", date)
        return date
    dbg("CLEAN_DATE_FAIL", txt)
    return ""

def clean_sex(txt):
    t = txt.strip().upper()
    if t == "M":
        dbg("CLEAN_SEX", "MALE")
        return "MALE"
    if t == "F":
        dbg("CLEAN_SEX", "FEMALE")
        return "FEMALE"
    dbg("CLEAN_SEX_FAIL", txt)
    return ""

# =========================
# MAIN PROCESSOR
# =========================
def process_driving_license(image_rgb, model, reader, conf=0.35, iou=0.45):

    dbg("PROCESS_START", {
        "conf": conf,
        "iou": iou,
        "image_shape": image_rgb.shape
    })

    results = model.predict(image_rgb, conf=conf, iou=iou, verbose=False)
    boxes = results[0].boxes
    names = model.names

    dbg("YOLO_RESULT", {
        "total_boxes": len(boxes),
        "classes": [names[int(b.cls.item())] for b in boxes]
    })

    data = {
        "StateName": "",
        "address": "",
        "dateOfBirth": "",
        "firstName": "",
        "lastName": "",
        "licenseNumber": "",
        "sex": ""
    }

    for idx, box in enumerate(boxes):
        cls = names[int(box.cls.item())]

        dbg("YOLO_BOX_START", {
            "index": idx,
            "class": cls
        })

        if cls not in data:
            dbg("SKIP_CLASS_NOT_USED", cls)
            continue

        x1, y1, x2, y2 = box.xyxy.cpu().numpy().astype(int).reshape(-1)

        dbg("BOX_COORD", [x1, y1, x2, y2])

        # safety crop
        h, w, _ = image_rgb.shape
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        crop = image_rgb[y1:y2, x1:x2]

        if crop.size == 0:
            dbg("EMPTY_CROP", cls)
            continue

        raw = read_text(crop, reader)
        txt = re.sub(r"[^A-Za-z0-9\s/]", "", raw).strip()

        dbg("OCR_FINAL_TEXT", {
            "class": cls,
            "raw": raw,
            "clean": txt
        })

        if not txt:
            dbg("SKIP_EMPTY_TEXT", cls)
            continue

        # ===== FIELD HANDLING =====
        if cls == "licenseNumber":
            txt = clean_license_number(txt)

        elif cls == "sex":
            txt = clean_sex(txt)

        elif cls == "dateOfBirth":
            d = clean_date(txt)
            if d:
                data["dateOfBirth"] = d
                dbg("FIELD_SET", {"dateOfBirth": d})
            else:
                dbg("FIELD_FAIL", "dateOfBirth")
            continue

        if not data[cls]:
            data[cls] = txt.upper()
            dbg("FIELD_SET", {cls: data[cls]})
        else:
            dbg("FIELD_ALREADY_FILLED", {cls: data[cls]})

    dbg("PROCESS_RESULT", data)

    dbg("MISSING_FIELDS", [k for k,v in data.items() if not v])

    # =========================
    # FACE EXTRACTION (GENERAL)
    # =========================
    try:
        state = data.get("StateName")  # bisa None / ""

        face_img = crop_face_by_state(image_rgb, state)
        face_b64 = face_to_base64(face_img)

        data["faceImage"] = face_b64

        dbg("FACE_EXTRACTED", {
            "state": state or "GENERAL",
            "face_size": face_img.size
        })

    except Exception as e:
        dbg("FACE_EXTRACT_FAIL", str(e))
        data["faceImage"] = ""

    return data

