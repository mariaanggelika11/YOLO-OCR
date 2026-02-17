import cv2
import base64
import io
from PIL import Image

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def detect_and_crop_face(image_rgb):
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    if len(faces) == 0:
        return None

    # Ambil wajah terbesar
    faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
    x, y, w, h = faces[0]

    # =========================
    # TAMBAH MARGIN (ZOOM OUT)
    # =========================
    padding_x = int(w * 0.25)   # 25% kiri kanan
    padding_y = int(h * 0.35)   # 35% atas bawah

    x1 = max(0, x - padding_x)
    y1 = max(0, y - padding_y)
    x2 = min(image_rgb.shape[1], x + w + padding_x)
    y2 = min(image_rgb.shape[0], y + h + padding_y)

    img = Image.fromarray(image_rgb)
    face = img.crop((x1, y1, x2, y2))

    return face

def face_to_base64(face_img: Image.Image):
    buf = io.BytesIO()
    face_img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
