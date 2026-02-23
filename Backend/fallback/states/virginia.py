import re
from datetime import datetime
from fallback.config import VALID_STATES, NAME_BLACKLIST

DEBUG = True

def dbg(tag, payload=None):
    if not DEBUG:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[VA_STATE {ts}] {tag}")
    if payload is not None:
        if isinstance(payload, (list, dict)):
            import json
            print(json.dumps(payload, indent=2))
        else:
            print(payload)


# =========================
# LICENSE FORMATTER (VA)
# =========================
def format_va_license(raw: str) -> str:
    if not raw:
        return raw

    raw = re.sub(r"[^A-Z0-9]", "", raw.upper())

    if re.fullmatch(r"[A-Z]\d{8}", raw):
        return raw

    return raw


# =========================
# DOB VALIDATOR
# =========================
def is_valid_dob(date_str):
    try:
        d, m, y = map(int, date_str.split("/"))
        year_now = datetime.now().year

        if y < 1900:
            return False

        if y > year_now:
            return False

        age = year_now - y

        if age < 15 or age > 100:
            return False

        return True
    except:
        return False


# =========================
# ENRICH (ALWAYS RUN)
# =========================
def enrich(data):

    dbg("ENRICH_START", data)

    if data.get("licenseNumber"):
        formatted = format_va_license(data["licenseNumber"])
        if formatted != data["licenseNumber"]:
            dbg("LICENSE_FORMAT_VA", {
                "before": data["licenseNumber"],
                "after": formatted
            })
            data["licenseNumber"] = formatted

    dbg("ENRICH_RESULT", data)
    return data


# =========================
# FALLBACK OCR
# =========================
def apply(image_rgb, reader, data):

    dbg("FALLBACK_START", data)

    lines = reader.readtext(image_rgb, detail=0, paragraph=False)
    dbg("OCR_LINES", lines)

    # =====================
    # STATE
    # =====================
    if not data.get("StateName"):
        for l in lines:
            if "VIRGINIA" in l.upper():
                data["StateName"] = "VIRGINIA"
                dbg("STATE_FOUND", "VIRGINIA")
                break

    # =====================
    # LICENSE NUMBER
    # =====================
    if not data.get("licenseNumber"):
        for l in lines:
            t = re.sub(r"[^A-Z0-9]", "", l.upper())
            if re.fullmatch(r"[A-Z]\d{8}", t):
                data["licenseNumber"] = format_va_license(t)
                dbg("LICENSE_FOUND_FALLBACK", data["licenseNumber"])
                break

    # =====================
    # DOB (ANTI-EXP SAFE)
    # =====================
    if not data.get("dateOfBirth"):

        dob_candidates = []

        for l in lines:
            matches = re.findall(r"(\d{2})[\/\-.](\d{2})[\/\-.](\d{4})", l)

            for d, m_, y in matches:
                candidate = f"{d}/{m_}/{y}"

                if is_valid_dob(candidate):
                    dob_candidates.append(candidate)

        dbg("DOB_CANDIDATES_VALID", dob_candidates)

        if dob_candidates:
            dob_candidates.sort(key=lambda x: int(x.split("/")[-1]))
            data["dateOfBirth"] = dob_candidates[0]
            dbg("DOB_SELECTED", data["dateOfBirth"])

    # =====================
    # SEX
    # =====================
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

    # =====================
    # NAME EXTRACTION (FIXED)
    # =====================
    if not data.get("firstName") or not data.get("lastName"):

        single_words = []
        multi_words = []

        for l in lines:
            original = l.strip()

            # Harus benar-benar ALL CAPS asli
            if original != original.upper():
                continue

            # Hanya huruf & spasi
            if not re.fullmatch(r"[A-Z ]+", original):
                continue

            # Skip state
            if original in VALID_STATES:
                continue

            # Skip blacklist
            if original in NAME_BLACKLIST:
                continue

            words = original.split()

            if len(words) == 1:
                single_words.append(original)
            elif len(words) >= 2:
                multi_words.append(original)

        dbg("NAME_SINGLE_WORDS", single_words)
        dbg("NAME_MULTI_WORDS", multi_words)

        # Last name → single word pertama
        if not data.get("lastName") and single_words:
            data["lastName"] = single_words[0]
            dbg("LASTNAME_SET", data["lastName"])

        # First name logic
        if not data.get("firstName"):

            if multi_words:
                data["firstName"] = multi_words[0]
                dbg("FIRSTNAME_SET", data["firstName"])

            elif len(single_words) >= 2:
                data["firstName"] = single_words[1]
                dbg("FIRSTNAME_SET", data["firstName"])

            elif len(single_words) == 1:
                data["firstName"] = single_words[0]
                dbg("FIRSTNAME_SET_SINGLE", data["firstName"])

    dbg("FALLBACK_RESULT", data)
    return data