import re

def apply(image_rgb, reader, data):

    lines = reader.readtext(image_rgb, detail=0, paragraph=False)

    if not data["dateOfBirth"]:
        for l in lines:
            if "DOB" in l.upper():
                m = re.search(r"\d{2}/\d{2}/\d{4}", l)
                if m:
                    data["dateOfBirth"] = m.group(0)

    return data
