import re
from datetime import datetime
from fallback.config import VALID_STATES, NAME_BLACKLIST

DEBUG = True

def dbg(tag, payload=None):
    if not DEBUG:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[MD_STATE {ts}] {tag}")
    if payload is not None:
        if isinstance(payload, (list, dict)):
            import json
            print(json.dumps(payload, indent=2))
        else:
            print(payload)

# =========================
# LICENSE FORMATTER (MD)
# =========================
def format_md_license(raw: str) -> str:
    """
    Maryland DL format:
    B435257021012 -> B-435-257-021-012
    """
    if not raw:
        return raw

    raw = raw.replace("-", "").replace(" ", "").upper()

    if not re.fullmatch(r"[A-Z]\d{12}", raw):
        return raw

    return f"{raw[0]}-{raw[1:4]}-{raw[4:7]}-{raw[7:10]}-{raw[10:13]}"

# =========================
# ENRICH (SELALU JALAN)
# =========================
def enrich(data):
    """
    Cleansing & formatting khusus Maryland
    DIPANGGIL WALAU YOLO SUKSES
    """

    dbg("ENRICH_START", data)

    if data.get("licenseNumber"):
        formatted = format_md_license(data["licenseNumber"])
        if formatted != data["licenseNumber"]:
            dbg("LICENSE_FORMAT_MD", {
                "before": data["licenseNumber"],
                "after": formatted
            })
            data["licenseNumber"] = formatted

    dbg("ENRICH_RESULT", data)
    return data

# =========================
# FALLBACK OCR (OPTIONAL)
# =========================
def apply(image_rgb, reader, data):
    """
    HANYA untuk isi field yang kosong
    """

    dbg("FALLBACK_START", data)

    lines = reader.readtext(image_rgb, detail=0, paragraph=False)
    dbg("OCR_LINES", lines)

    # STATE
    if not data.get("StateName"):
        for l in lines:
            if "MARYLAND" in l.upper():
                data["StateName"] = "MARYLAND"
                dbg("STATE_FOUND", "MARYLAND")
                break

    # DOB
    if not data.get("dateOfBirth"):
        for l in lines:
            m = re.search(r"(\d{2})[\/\-.](\d{2})[\/\-.](\d{4})", l)
            if m:
                d, m_, y = m.groups()
                data["dateOfBirth"] = f"{d}/{m_}/{y}"
                dbg("DOB_FOUND", data["dateOfBirth"])
                break

    # SEX
    if not data.get("sex"):
        for l in lines:
            t = l.strip().upper()
            if t in ("M", "MALE"):
                data["sex"] = "MALE"
                dbg("SEX_FOUND", "MALE")
                break
            if t in ("F", "FEMALE"):
                data["sex"] = "FEMALE"
                dbg("SEX_FOUND", "FEMALE")
                break

    # LICENSE NUMBER (kalau YOLO gagal)
    if not data.get("licenseNumber"):
        for l in lines:
            t = re.sub(r"[^A-Z0-9]", "", l.upper())
            if re.fullmatch(r"[A-Z]\d{12}", t):
                data["licenseNumber"] = format_md_license(t)
                dbg("LICENSE_FOUND_FALLBACK", data["licenseNumber"])
                break

    # NAME
    if not data.get("firstName") or not data.get("lastName"):
        candidates = []

    for l in lines:
        t = l.strip().upper()

        if not t.isalpha():
            continue
        if len(t) < 3:
            continue
        if any(state in t for state in VALID_STATES):
            continue
        if t in NAME_BLACKLIST:
            continue
        if not t.isupper():
            continue

        candidates.append(t)

    dbg("NAME_CANDIDATES_FILTERED", candidates)

    # LAST NAME = kata ALL CAPS pertama
    if candidates and not data.get("lastName"):
        data["lastName"] = candidates[0]
        dbg("LASTNAME_SET", data["lastName"])

    # FIRST NAME
    if not data.get("firstName"):
        if "FNU" in candidates:
            data["firstName"] = "FNU"
            dbg("FIRSTNAME_SET", "FNU")
        elif len(candidates) > 1:
            data["firstName"] = candidates[1]
            dbg("FIRSTNAME_SET", data["firstName"])

    dbg("FALLBACK_RESULT", data)
    return data
