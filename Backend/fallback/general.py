import re
from datetime import datetime
from fallback.config import VALID_STATES, NAME_BLACKLIST

# =========================
# DEBUG HELPER
# =========================
DEBUG = True

def dbg(tag, payload=None):
    if not DEBUG:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[GENERAL_FALLBACK {ts}] {tag}")
    if payload is not None:
        if isinstance(payload, (list, dict)):
            import json
            print(json.dumps(payload, indent=2))
        else:
            print(payload)

# =========================
# MAIN FALLBACK
# =========================
def apply(image_rgb, reader, data):

    dbg("START_DATA", data)

    lines = reader.readtext(image_rgb, detail=0, paragraph=False)
    dbg("OCR_LINE_COUNT", len(lines))
    dbg("OCR_LINES", lines)

    # =========================
    # STATE
    # =========================
    if not data.get("StateName"):
        for l in lines:
            u = l.strip().upper()
            if u in VALID_STATES:
                data["StateName"] = u
                dbg("STATE_FOUND", u)
                break

        if not data.get("StateName"):
            dbg("STATE_NOT_FOUND", None)

    # =========================
    # DATE OF BIRTH
    # support: 01/02/1999 | 01-02-1999 | 01.02.1999
    # =========================
    if not data.get("dateOfBirth"):
        for l in lines:
            m = re.search(r"(\d{2})[\/\-.](\d{2})[\/\-.](\d{4})", l)
            if m:
                d, m_, y = m.groups()
                data["dateOfBirth"] = f"{d}/{m_}/{y}"
                dbg("DOB_FOUND", data["dateOfBirth"])
                break

        if not data.get("dateOfBirth"):
            dbg("DOB_NOT_FOUND", None)

    # =========================
    # SEX
    # =========================
    if not data.get("sex"):
        for l in lines:
            s = l.strip().upper()
            if s in ("M", "MALE"):
                data["sex"] = "MALE"
                dbg("SEX_FOUND", "MALE")
                break
            elif s in ("F", "FEMALE"):
                data["sex"] = "FEMALE"
                dbg("SEX_FOUND", "FEMALE")
                break

        if not data.get("sex"):
            dbg("SEX_NOT_FOUND", None)

    # =========================
    # NAME FALLBACK
    # =========================
    if not data.get("firstName") or not data.get("lastName"):
        candidates = []

        for l in lines:
            t = l.strip().upper()

            if not t.isalpha():
                continue
            if len(t) <= 2:
                continue
            if t in NAME_BLACKLIST:
                continue
            if t in VALID_STATES:
                continue

            candidates.append(t)

        dbg("NAME_CANDIDATES", candidates)

        if candidates:
            if not data.get("lastName"):
                data["lastName"] = candidates[0]
                dbg("LASTNAME_SET", data["lastName"])

            if not data.get("firstName") and len(candidates) > 1:
                data["firstName"] = candidates[1]
                dbg("FIRSTNAME_SET", data["firstName"])

    # =========================
    # RESULT
    # =========================
    dbg("FINAL_DATA", data)
    dbg("MISSING_FIELDS", [k for k, v in data.items() if not v])

    return data
