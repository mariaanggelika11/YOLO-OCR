import re
import difflib
from datetime import datetime
from fallback.config import VALID_STATES, NAME_BLACKLIST

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

def find_state(lines):
    for l in lines:
        u = l.strip().upper()
        if u in VALID_STATES:
            return u

    for l in lines:
        u = l.strip().upper()
        if len(u) < 4:
            continue
        match = difflib.get_close_matches(u, VALID_STATES, n=1, cutoff=0.75)
        if match:
            return match[0]

    return None

def apply(image_rgb, reader, data):

    dbg("START_DATA", data)

    lines = reader.readtext(image_rgb, detail=0, paragraph=False)
    dbg("OCR_LINE_COUNT", len(lines))
    dbg("OCR_LINES", lines)

    if not data.get("StateName"):
        state = find_state(lines)
        if state:
            data["StateName"] = state
            dbg("STATE_FOUND", state)
        else:
            dbg("STATE_NOT_FOUND", None)

    if not data.get("dateOfBirth"):
        for l in lines:
            m = re.search(r"(\d{2})[\/\-.](\d{2})[\/\-.](\d{4})", l)
            if m:
                d, m_, y = m.groups()
                data["dateOfBirth"] = f"{d}/{m_}/{y}"
                dbg("DOB_FOUND", data["dateOfBirth"])
                break

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

    if not data.get("firstName") or not data.get("lastName"):

        single_words = []
        multi_words = []

        for l in lines:
            original = l.strip()

            if original != original.upper():
                continue

            if not re.fullmatch(r"[A-Z ]+", original):
                continue

            if original in VALID_STATES:
                continue

            if original in NAME_BLACKLIST:
                continue

            words = original.split()

            if len(words) == 1:
                single_words.append(original)
            elif len(words) >= 2:
                multi_words.append(original)

        dbg("NAME_SINGLE_WORDS", single_words)
        dbg("NAME_MULTI_WORDS", multi_words)

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

    dbg("FINAL_DATA", data)
    dbg("MISSING_FIELDS", [k for k, v in data.items() if not v])

    return data