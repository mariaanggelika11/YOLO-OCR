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

def enrich(data):
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

def apply(image_rgb, reader, data):

    dbg("FALLBACK_START", data)

    lines = reader.readtext(image_rgb, detail=0, paragraph=False)
    dbg("OCR_LINES", lines)

    if not data.get("StateName"):
        for l in lines:
            if "WEST VIRGINIA" in l.upper():
                data["StateName"] = "WEST VIRGINIA"
                dbg("STATE_FOUND", "WEST VIRGINIA")
                break

    if not data.get("licenseNumber"):
        for l in lines:
            t = re.sub(r"[^A-Z0-9]", "", l.upper())
            if re.fullmatch(r"[A-Z]\d{6}", t):
                data["licenseNumber"] = t
                dbg("LICENSE_FOUND", t)
                break

    if not data.get("dateOfBirth"):
        for l in lines:
            m = re.search(r"(\d{2}/\d{2}/\d{4})", l)
            if m:
                data["dateOfBirth"] = m.group(1)
                dbg("DOB_FOUND", data["dateOfBirth"])
                break

    if not data.get("sex"):
        for l in lines:
            m = re.search(r"\bSEX\b[:\s]*([MF])", l.upper())
            if m:
                data["sex"] = "MALE" if m.group(1) == "M" else "FEMALE"
                dbg("SEX_FOUND", data["sex"])
                break

    if not data.get("firstName") or not data.get("lastName"):

        single_words = []
        multi_words = []

        for l in lines:
            original = l.strip()

            if original != original.upper():
                continue

            if not re.fullmatch(r"[A-Z0-9\.\,\s]+", original):
                continue

            if original in VALID_STATES:
                continue

            if original in NAME_BLACKLIST:
                continue

            if re.match(r"1\.\s*[A-Z ]+", original) and not data.get("lastName"):
                lastname = re.sub(r"1\.\s*", "", original)
                data["lastName"] = lastname.strip()
                dbg("LASTNAME_FOUND", data["lastName"])
                continue

            if re.match(r"2\.\s*[A-Z ,]+", original) and not data.get("firstName"):
                first_part = re.sub(r"2\.\s*", "", original)
                first = first_part.split(",")[0].strip()
                data["firstName"] = first
                dbg("FIRSTNAME_FOUND", data["firstName"])
                continue

            clean = re.sub(r"[^\sA-Z]", "", original).strip()
            if not clean:
                continue

            words = clean.split()

            if len(words) == 1:
                single_words.append(clean)
            elif len(words) >= 2:
                multi_words.append(clean)

        if not data.get("lastName") and single_words:
            data["lastName"] = single_words[0]
            dbg("LASTNAME_SET", data["lastName"])

        if not data.get("firstName"):
            if multi_words:
                data["firstName"] = multi_words[0]
                dbg("FIRSTNAME_SET", data["firstName"])
            elif len(single_words) >= 2:
                data["firstName"] = single_words[1]
                dbg("FIRSTNAME_SET", data["firstName"])

    dbg("FALLBACK_RESULT", data)
    return data