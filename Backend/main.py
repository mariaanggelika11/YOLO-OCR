import io, base64, os
import cv2
import numpy as np
import pytesseract
import easyocr
import re

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

from processors.passport_processor import process_passport
from processors.dl_processor import process_driving_license
from processors.face_extractor import detect_and_crop_face, face_to_base64
from fallback.router import apply_fallback

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

passport_model = YOLO("models/passport_model.pt")
driving_model = YOLO("models/dl_model.pt")
reader = easyocr.Reader(['en'])


def extract_text(img: np.ndarray) -> str:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray).lower()


def detect_doc_type(img: np.ndarray, text: str):

    passport_boxes = passport_model.predict(
        img, conf=0.25, iou=0.35, verbose=False
    )[0].boxes or []

    driving_boxes = driving_model.predict(
        img, conf=0.25, iou=0.35, verbose=False
    )[0].boxes or []

    if len(passport_boxes) > len(driving_boxes):
        return "passport"
    return "driving_license"


@app.post("/detect")
async def detect_document(file: UploadFile = File(...)):

    contents = await file.read()
    img = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    text = extract_text(img)

    doc_type = detect_doc_type(img_rgb, text)

    # =========================
    # DOCUMENT PROCESSING
    # =========================
    if doc_type == "passport":
        parsed = process_passport(
            img_rgb, passport_model, reader
        )
    else:
        parsed = process_driving_license(
            img_rgb, driving_model, reader
        )

    # =========================
    # FACE DETECTION
    # =========================
    face_image = detect_and_crop_face(img_rgb)
    face_base64 = None

    if face_image:
        face_base64 = face_to_base64(face_image)

    # =========================
    # FALLBACK PIPELINE
    # =========================
    parsed = apply_fallback(img_rgb, reader, parsed)

    return JSONResponse({
        "success": True,
        "detected_type": doc_type,
        "face": face_base64,
        "parsed": parsed
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
