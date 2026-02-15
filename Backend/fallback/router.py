from fallback.states import (
    maryland,
    virginia,
    newyork,
    pennsylvania,
    delaware,
    westvirginia
)
from fallback import general


def apply_fallback(image_rgb, reader, data):

    state = data.get("StateName", "").strip().upper()

    # =========================
    # ENRICH (SELALU DIJALANKAN)
    # =========================
    if state == "WEST VIRGINIA":
        data = westvirginia.enrich(data)

    elif state == "VIRGINIA":
        data = virginia.enrich(data)

    elif state == "MARYLAND":
        data = maryland.enrich(data)

    elif state == "NEW YORK":
        data = newyork.enrich(data)

    elif state == "PENNSYLVANIA":
        data = pennsylvania.enrich(data)

    elif state == "DELAWARE":
        data = delaware.enrich(data)

    # =========================
    # STATE FALLBACK (ONLY IF FIELD EMPTY)
    # =========================
    has_missing = any(v == "" for v in data.values())

    if has_missing:

        if state == "WEST VIRGINIA":
            data = westvirginia.apply(image_rgb, reader, data)

        elif state == "VIRGINIA":
            data = virginia.apply(image_rgb, reader, data)

        elif state == "MARYLAND":
            data = maryland.apply(image_rgb, reader, data)

        elif state == "NEW YORK":
            data = newyork.apply(image_rgb, reader, data)

        elif state == "PENNSYLVANIA":
            data = pennsylvania.apply(image_rgb, reader, data)

        elif state == "DELAWARE":
            data = delaware.apply(image_rgb, reader, data)

    # =========================
    # GENERAL FALLBACK (LAST DEFENSE)
    # =========================
    if any(v == "" for v in data.values()):
        data = general.apply(image_rgb, reader, data)

    return data
