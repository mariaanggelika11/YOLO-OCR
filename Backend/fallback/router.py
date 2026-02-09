from fallback.states import maryland, virginia, newyork
from fallback import general

def apply_fallback(image_rgb, reader, data):

    state = data.get("StateName", "").upper()

    # =========================
    # STATE ENRICH (SELALU)
    # =========================
    if "MARYLAND" in state:
        data = maryland.enrich(data)

    elif "VIRGINIA" in state:
        data = virginia.enrich(data)

    elif "NEW YORK" in state:
        data = newyork.enrich(data)

    # =========================
    # STATE FALLBACK (KALAU KOSONG)
    # =========================
    if "MARYLAND" in state and any(v == "" for v in data.values()):
        data = maryland.apply(image_rgb, reader, data)

    elif "VIRGINIA" in state and any(v == "" for v in data.values()):
        data = virginia.apply(image_rgb, reader, data)

    elif "NEW YORK" in state and any(v == "" for v in data.values()):
        data = newyork.apply(image_rgb, reader, data)

    # =========================
    # GENERAL FALLBACK (LAST)
    # =========================
    if any(v == "" for v in data.values()):
        data = general.apply(image_rgb, reader, data)

    return data
