import React, { useState, useRef } from "react";
import { Camera, Upload, Loader } from "lucide-react";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  `${window.location.protocol}//${window.location.hostname}:8000`;

interface ExtractedData {
  firstName: string;
  lastName: string;
  address: string;
  dob: string;
  sex: string;
  nationality: string;
  passportNumber: string;
  licenseNumber: string;
  faceImage?: string;
}

interface CameraCaptureProps {
  onExtractedData: (data: Partial<ExtractedData>) => void;
}

const CameraCapture: React.FC<CameraCaptureProps> = ({ onExtractedData }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef<HTMLDivElement>(null);

  const [isCameraOn, setIsCameraOn] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // =========================
  // START CAMERA (LANDSCAPE FOR DL)
  // =========================
  const startCamera = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment",
          aspectRatio: 1.585, // DL ratio
          width: { ideal: 1280 },
          height: { ideal: 800 },
        },
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsCameraOn(true);
      }
    } catch {
      setError("Cannot access camera");
    }
  };

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
    }
    setIsCameraOn(false);
  };

  // =========================
  // CAPTURE BASED ON FRAME %
  // =========================
const capturePhoto = () => {
  const video = videoRef.current;
  const canvas = canvasRef.current;

  if (!video || !canvas) return;

  const vw = video.videoWidth;
  const vh = video.videoHeight;

  const frameWidthRatio = 0.9; // sama seperti overlay 90%
  const targetAspect = 1.585;

  const cropWidth = vw * frameWidthRatio;
  const cropHeight = cropWidth / targetAspect;

  const cropX = (vw - cropWidth) / 2;
  const cropY = (vh - cropHeight) / 2;

  canvas.width = cropWidth;
  canvas.height = cropHeight;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  ctx.drawImage(
    video,
    cropX,
    cropY,
    cropWidth,
    cropHeight,
    0,
    0,
    cropWidth,
    cropHeight
  );

  const cropped = canvas.toDataURL("image/jpeg", 0.95);

  console.log("Cropped resolution:", cropWidth, cropHeight);

  setPreviewImage(cropped);
  stopCamera();
};

  // =========================
  // UPLOAD
  // =========================
  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError("");
    if (!e.target.files?.length) return;

    const reader = new FileReader();
    reader.onload = () => {
      setPreviewImage(reader.result as string);
    };
    reader.readAsDataURL(e.target.files[0]);
  };

  // =========================
  // SEND BACKEND
  // =========================
  const sendToBackend = async () => {
    if (!previewImage) return;

    setLoading(true);
    setError("");

    try {
      const blob = await (await fetch(previewImage)).blob();
      const formData = new FormData();
      formData.append("file", blob, "document.jpg");

      const res = await fetch(`${API_BASE_URL}/detect`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      onExtractedData(data.parsed);
    } catch (err: any) {
      setError(err.message);
    }

    setLoading(false);
  };

  const reset = () => {
    setPreviewImage(null);
    setError("");
  };

  return (
    <div className="bg-white p-6 rounded-2xl shadow-xl w-full max-w-lg flex flex-col gap-4">

      <h2 className="text-xl font-bold text-gray-800 flex items-center gap-3">
        <div className="bg-indigo-600 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold">
          1
        </div>
        Scan Document
      </h2>

      {/* CONTAINER DL RATIO */}
      <div className="relative w-full aspect-[1.585/1] bg-black rounded-xl overflow-hidden">

        {previewImage ? (
          <img
            src={previewImage}
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className={`absolute inset-0 w-full h-full object-cover ${
                isCameraOn ? "opacity-100" : "opacity-0"
              }`}
            />

            {isCameraOn && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div
                  ref={frameRef}
                  className="relative w-[90%] aspect-[1.585/1] border-2 border-green-500 rounded-xl"
                  style={{
                    boxShadow: "0 0 0 9999px rgba(0,0,0,0.65)",
                  }}
                />
              </div>
            )}
          </>
        )}

        {loading && (
          <div className="absolute inset-0 bg-black/70 flex items-center justify-center">
            <Loader className="animate-spin text-white" />
          </div>
        )}
      </div>

      <canvas ref={canvasRef} className="hidden" />

      {error && (
        <div className="bg-red-100 text-red-700 p-2 rounded text-sm">
          {error}
        </div>
      )}

      {!previewImage && (
        <div className="flex gap-3">
          <button
            onClick={startCamera}
            className="flex items-center justify-center gap-2 flex-1 bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-lg transition"
          >
            <Camera size={18} />
            Camera
          </button>

          <label className="flex items-center justify-center gap-2 flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 py-3 rounded-lg cursor-pointer transition">
            <Upload size={18} />
            Upload
            <input
              type="file"
              accept="image/*"
              onChange={handleUpload}
              className="hidden"
            />
          </label>
        </div>
      )}

      {isCameraOn && !previewImage && (
        <button
          onClick={capturePhoto}
          className="bg-red-500 hover:bg-red-600 text-white py-3 rounded-lg transition"
        >
          Capture
        </button>
      )}

      {previewImage && (
        <>
          <button
            onClick={sendToBackend}
            className="bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-lg transition"
          >
            Process
          </button>

          <button
            onClick={reset}
            className="bg-gray-500 hover:bg-gray-600 text-white py-2 rounded-lg transition"
          >
            Retake
          </button>
        </>
      )}
    </div>
  );
};

export default CameraCapture;
