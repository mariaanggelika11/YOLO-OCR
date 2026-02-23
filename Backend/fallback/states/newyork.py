import re
from datetime import datetime
from fallback.config import VALID_STATES, NAME_BLACKLIST

DEBUG = True

def dbg(tag, payload=None):
    if not DEBUG:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[NY_STATE {ts}] {tag}")
    if payload is not None:
        if isinstance(payload, (list, dict)):
            import json
            print(json.dumps(payload, indent=2))
        else:
            print(payload)

def enrich(data):
    dbg("ENRICH_START", data)

    lic = data.get("licenseNumber", "")
    if lic:
        lic = lic.replace(" ", "").upper()

        if re.fullmatch(r"\d{9}", lic) or re.fullmatch(r"[A-Z]\d{8}", lic):
            data["licenseNumber"] = lic
            dbg("LICENSE_OK", lic)
        else:
            dbg("LICENSE_SUSPECT", lic)

    dbg("ENRICH_RESULT", data)
    return data

def apply(image_rgb, reader, data):
    """
    New York fallback:
    - HANYA mengisi field kosong
    - Tidak overwrite hasil YOLO
    """

    dbg("FALLBACK_START", data)

    lines = reader.readtext(image_rgb, detail=0, paragraph=False)
    dbg("OCR_LINES", lines)

    if not data.get("StateName"):
        for l in lines:
            if "NEW YORK" in l.upper():
                data["StateName"] = "NEW YORK STATE"
                dbg("STATE_FOUND", data["StateName"])
                break

    if not data.get("sex"):
        for i, l in enumerate(lines):
            t = l.strip().upper()

            m = re.search(r"\bSEX\b\s*[:\-]?\s*([MF])\b", t)
            if m:
                data["sex"] = "MALE" if m.group(1) == "M" else "FEMALE"
                dbg("SEX_FOUND_INLINE", data["sex"])
                break

            if t == "SEX":
                for j in range(i + 1, min(i + 3, len(lines))):
                    nxt = lines[j].strip().upper()
                    if nxt == "M":
                        data["sex"] = "MALE"
                        dbg("SEX_FOUND_NEXT_LINE", "MALE")
                        break
                    if nxt == "F":
                        data["sex"] = "FEMALE"
                        dbg("SEX_FOUND_NEXT_LINE", "FEMALE")
                        break
                if data.get("sex"):
                    break

            if t == "M":
                data["sex"] = "MALE"
                dbg("SEX_FOUND_STANDALONE", "MALE")
                break
            if t == "F":
                data["sex"] = "FEMALE"
                dbg("SEX_FOUND_STANDALONE", "FEMALE")
                break

    if not data.get("licenseNumber"):
        for l in lines:
            t = re.sub(r"[^A-Z0-9]", "", l.upper())

            if re.fullmatch(r"\d{9}", t) or re.fullmatch(r"[A-Z]\d{8}", t):
                data["licenseNumber"] = t
                dbg("LICENSE_FOUND_FALLBACK", t)
                break

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
            if t == "FNU":
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
    dbg("MISSING_FIELDS", [k for k, v in data.items() if not v])

    return data
