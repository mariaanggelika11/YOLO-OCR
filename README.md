# YOLO OCR

YOLO OCR is a document OCR system built using **YOLO**, **EasyOCR**, and **Tesseract**.  
It is designed to extract structured data from official identity documents such as:

- **Driver License (United States)**
- **Passport** (basic support)

This project uses **YOLO** for field detection, **OCR** for text recognition, and
**state-based fallback logic** to keep results consistent even when OCR or models
are not perfect.

---

## Key Features

### Backend (Python + FastAPI)

- **YOLOv8 field detection**
  - `licenseNumber`
  - `firstName`
  - `lastName`
  - `address`
  - `dateOfBirth`
  - `sex`
  - `StateName`
  - `faceImage` (auto-cropped photo)

- **OCR**
  - EasyOCR as primary OCR engine
  - Tesseract as fallback OCR

- **Fallback Logic**
  - State-specific fallback:
    - Maryland
    - New York
    - Virginia
  - General fallback if fields are still missing

- **Automatic face photo crop**
  - Face/photo region is cropped on backend
  - Returned as Base64 image

- **Detailed debug logging**
  - Step-by-step logs for easier analysis and debugging

---

### Frontend (Vite + React + TailwindCSS)

- Upload document image
- Live camera capture
- Document alignment guide box
- Image preview
- Display extracted data
- Display auto-cropped face photo
- Still in development (not production-ready UI)

---

## Automatic Face Image Crop

The backend **automatically extracts and crops the face photo** from supported documents
(e.g. Driver License).

### Flow

1. YOLO detects the **photo / face region** on the document.
2. Backend crops the detected region.
3. Cropped image is:
   - Converted to **JPEG**
   - Encoded as **Base64**
4. Returned inside the API response as `faceImage`.

### Frontend Responsibility

- Frontend **does not crop the face manually**
- Frontend only needs to render:
  ```html
  <img src="data:image/jpeg;base64,{faceImage}" />


YOLO-OCR/
├── Backend/
│   ├── fallback/
│   │   ├── states/
│   │   │   ├── maryland.py
│   │   │   ├── virginia.py
│   │   │   ├── newyork.py
│   │   │   └── config.py
│   │   ├── general.py
│   │   └── router.py
│   │
│   ├── models/
│   │   ├── dl_model.pt
│   │   └── passport_model.pt
│   │
│   ├── processors/
│   │   ├── dl_processor.py
│   │   └── passport_processor.py
│   │
│   ├── main.py
│   ├── requirements.txt
│   └── .gitignore
│
├── Frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   ├── index.html
│   ├── eslint.config.js
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── README.md
│
└── README.md

At the moment, this project still uses a hardcoded Tesseract path for local development on Windows: pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe" This setup is temporary and only intended for local testing.


-Progressive Web App (PWA) Support
Run Backend
uvicorn main:app --host 0.0.0.0 --port 8000

Run Frontend
npm run dev

Open  HTTPS URL on your mobile device