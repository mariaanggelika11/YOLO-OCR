import re
import pytesseract
import numpy as np
from datetime import datetime
from processors.face_extractor import detect_and_crop_face, face_to_base64

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
        "sex": "",
        "faceImage": ""
    }

    for idx, box in enumerate(boxes):
        cls = names[int(box.cls.item())]

        if cls not in data:
            continue

        x1, y1, x2, y2 = box.xyxy.cpu().numpy().astype(int).reshape(-1)

        h, w, _ = image_rgb.shape
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        crop = image_rgb[y1:y2, x1:x2]

        if crop.size == 0:
            continue

        raw = read_text(crop, reader)
        txt = re.sub(r"[^A-Za-z0-9\s/]", "", raw).strip()

        if not txt:
            continue

        if cls == "licenseNumber":
            txt = clean_license_number(txt)

        elif cls == "sex":
            txt = clean_sex(txt)

        elif cls == "dateOfBirth":
            d = clean_date(txt)
            if not d:
                continue

            if not data["dateOfBirth"]:
                data["dateOfBirth"] = d
            else:
                old_year = int(data["dateOfBirth"].split("/")[-1])
                new_year = int(d.split("/")[-1])
                if new_year < old_year:
                    data["dateOfBirth"] = d
            continue

        if not data[cls]:
            data[cls] = txt.upper()

    # =========================
    # FACE EXTRACTION (NO DEBUG)
    # =========================
    try:
        face_img = detect_and_crop_face(image_rgb)
        if face_img:
            data["faceImage"] = face_to_base64(face_img)
    except:
        pass

    # Debug result TANPA base64
    safe_result = data.copy()
    safe_result["faceImage"] = "[HIDDEN]"
    dbg("PROCESS_RESULT", safe_result)

    return data
