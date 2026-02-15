import re
from datetime import datetime
from fallback.config import VALID_STATES, NAME_BLACKLIST

DEBUG = True

def dbg(tag, payload=None):
    if not DEBUG:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[WV_STATE {ts}] {tag}")
    if payload is not None:
        print(payload)


# ======================================================
# ENRICH
# ======================================================
def enrich(data):
    """
    West Virginia:
    License = 1 letter + 6 digits
    Example: Y999999
    """

    dbg("ENRICH_START", data)

    lic = data.get("licenseNumber", "")
    if lic:
        lic = re.sub(r"[^A-Z0-9]", "", lic.upper())

        if re.fullmatch(r"[A-Z]\d{6}", lic):
            data["licenseNumber"] = lic
            dbg("LICENSE_OK", lic)
        else:
            dbg("LICENSE_SUSPECT", lic)

    dbg("ENRICH_RESULT", data)
    return data


# ======================================================
# FALLBACK OCR
# ======================================================
def apply(image_rgb, reader, data):

    dbg("FALLBACK_START", data)

    lines = reader.readtext(image_rgb, detail=0, paragraph=False)
    dbg("OCR_LINES", lines)

    # =============================
    # STATE CONFIRMATION
    # =============================
    if not data.get("StateName"):
        for l in lines:
            if "WEST VIRGINIA" in l.upper():
                data["StateName"] = "WEST VIRGINIA"
                dbg("STATE_FOUND", "WEST VIRGINIA")
                break

    # =============================
    # LICENSE (Y999999)
    # =============================
    if not data.get("licenseNumber"):
        for l in lines:
            t = re.sub(r"[^A-Z0-9]", "", l.upper())
            if re.fullmatch(r"[A-Z]\d{6}", t):
                data["licenseNumber"] = t
                dbg("LICENSE_FOUND", t)
                break

    # =============================
    # DOB
    # =============================
    if not data.get("dateOfBirth"):
        for l in lines:
            m = re.search(r"DOB.*?(\d{2}/\d{2}/\d{4})", l.upper())
            if m:
                data["dateOfBirth"] = m.group(1)
                dbg("DOB_FOUND", data["dateOfBirth"])
                break

    # =============================
    # SEX
    # =============================
    if not data.get("sex"):
        for l in lines:
            m = re.search(r"SEX[:\s]*([MF])", l.upper())
            if m:
                data["sex"] = "MALE" if m.group(1) == "M" else "FEMALE"
                dbg("SEX_FOUND", data["sex"])
                break

    # =============================
    # NAME (1. LASTNAME / 2. FIRSTNAME, M)
    # =============================
    if not data.get("firstName") or not data.get("lastName"):

        for i, l in enumerate(lines):
            t = l.strip().upper()

            # LAST NAME (1. XXXXX)
            if re.match(r"1\.\s*[A-Z]+", t):
                lastname = re.sub(r"1\.\s*", "", t)
                data["lastName"] = lastname
                dbg("LASTNAME_FOUND", lastname)

            # FIRST NAME (2. TINA, A)
            if re.match(r"2\.\s*[A-Z]+", t):
                first_part = re.sub(r"2\.\s*", "", t)
                first = first_part.split(",")[0].strip()
                data["firstName"] = first
                dbg("FIRSTNAME_FOUND", first)

    dbg("FALLBACK_RESULT", data)
    return data
