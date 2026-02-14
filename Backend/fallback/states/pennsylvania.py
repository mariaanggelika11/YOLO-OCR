import re
from datetime import datetime
from fallback.config import VALID_STATES, NAME_BLACKLIST

DEBUG = True

def dbg(tag, payload=None):
    if not DEBUG:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[PA_STATE {ts}] {tag}")
    if payload is not None:
        print(payload)

# ======================================================
# ENRICH (Always run)
# ======================================================
def enrich(data):
    """
    Pennsylvania:
    License format = 8 digit numeric
    Example: 12345678
    """

    dbg("ENRICH_START", data)

    lic = data.get("licenseNumber", "")
    if lic:
        lic = re.sub(r"[^0-9]", "", lic)

        if re.fullmatch(r"\d{8}", lic):
            data["licenseNumber"] = lic
            dbg("LICENSE_OK", lic)
        else:
            dbg("LICENSE_SUSPECT", lic)

    dbg("ENRICH_RESULT", data)
    return data

# ======================================================
# FALLBACK OCR (PA)
# ======================================================
def apply(image_rgb, reader, data):

    dbg("FALLBACK_START", data)

    lines = reader.readtext(image_rgb, detail=0, paragraph=False)
    dbg("OCR_LINES", lines)

    # ==================================================
    # STATE CONFIRMATION
    # ==================================================
    if not data.get("StateName"):
        for l in lines:
            if "PENNSYLVANIA" in l.upper():
                data["StateName"] = "PENNSYLVANIA"
                dbg("STATE_FOUND", "PENNSYLVANIA")
                break

    # ==================================================
    # LICENSE NUMBER (8 digit numeric)
    # ==================================================
    if not data.get("licenseNumber"):
        for l in lines:
            t = re.sub(r"[^0-9]", "", l)
            if re.fullmatch(r"\d{8}", t):
                data["licenseNumber"] = t
                dbg("LICENSE_FOUND", t)
                break

    # ==================================================
    # DOB (08/04/1969)
    # ==================================================
    if not data.get("dateOfBirth"):
        for l in lines:
            m = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", l)
            if m:
                data["dateOfBirth"] = m.group(1)
                dbg("DOB_FOUND", data["dateOfBirth"])
                break

    # ==================================================
    # SEX (SEX: F)
    # ==================================================
    if not data.get("sex"):
        for l in lines:
            t = l.upper()
            m = re.search(r"\bSEX\b\s*[:\-]?\s*([MF])\b", t)
            if m:
                data["sex"] = "MALE" if m.group(1) == "M" else "FEMALE"
                dbg("SEX_FOUND", data["sex"])
                break

    # ==================================================
    # NAME
    # Layout:
    # SAMPLE
    # JANICE ANN
    # ==================================================
    if not data.get("firstName") or not data.get("lastName"):

        candidates = []

        for l in lines:
            t = l.strip().upper()

            if not t.isalpha():
                continue
            if len(t) < 3:
                continue
            if t in VALID_STATES:
                continue
            if t in NAME_BLACKLIST:
                continue

            candidates.append(t)

        dbg("NAME_CANDIDATES", candidates)

        if len(candidates) >= 2:
            if not data.get("lastName"):
                data["lastName"] = candidates[0]
                dbg("LASTNAME_SET", data["lastName"])

            if not data.get("firstName"):
                data["firstName"] = candidates[1]
                dbg("FIRSTNAME_SET", data["firstName"])

    dbg("FALLBACK_RESULT", data)
    return data
