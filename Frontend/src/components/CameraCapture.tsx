import React, { useState, useRef } from "react";
import { Camera, Upload, Loader, ScanLine } from "lucide-react";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  `${window.location.protocol}//${window.location.hostname}:8000`;

interface ExtractedData {
  firstName: string;
  lastName: string;
  address: string;
  dateOfBirth: string;  // ganti dari dob
  sex: string;
  nationality: string;
  passportNumber: string;
  licenseNumber: string;
  faceImage?: string;
}


interface Props {
  onExtractedData: (data: Partial<ExtractedData>) => void;
}

const CameraCapture: React.FC<Props> = ({ onExtractedData }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [isCameraOn, setIsCameraOn] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ================= START CAMERA =================
  const startCamera = async () => {
    setError("");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment",
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setIsCameraOn(true);
      }
    } catch {
      setError("Camera permission denied or unavailable");
    }
  };

  // ================= STOP CAMERA =================
  const stopCamera = () => {
    const stream = videoRef.current?.srcObject as MediaStream;
    if (stream) stream.getTracks().forEach((t) => t.stop());
    setIsCameraOn(false);
  };

  // ================= CAPTURE FULL IMAGE =================
  const capturePhoto = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const width = video.videoWidth;
    const height = video.videoHeight;

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // FULL FRAME — tidak crop
    ctx.drawImage(video, 0, 0, width, height);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        setCapturedBlob(blob);
        setPreviewImage(URL.createObjectURL(blob));
      },
      "image/jpeg",
      0.95
    );

    stopCamera();
  };

  // ================= UPLOAD =================
  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    const file = e.target.files[0];
    setCapturedBlob(file);
    setPreviewImage(URL.createObjectURL(file));
    stopCamera();
  };

  // ================= SEND BACKEND =================
  const sendToBackend = async () => {
    if (!capturedBlob) return;

    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", capturedBlob, "document.jpg");

      const res = await fetch(`${API_BASE_URL}/detect`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      onExtractedData(data.parsed);
    } catch (err: any) {
      setError(err.message || "Processing failed");
    }

    setLoading(false);
  };

  const reset = () => {
    if (previewImage) URL.revokeObjectURL(previewImage);
    setPreviewImage(null);
    setCapturedBlob(null);
  };

  return (
    <div className="bg-white p-6 rounded-2xl shadow-lg w-full max-w-lg">
    <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-3">
    <div className="bg-indigo-600 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold">
      1
    </div>
    Scan Document
  </h2>

      <div className="relative aspect-video bg-black rounded-xl overflow-hidden border">

        {/* PREVIEW */}
        {previewImage && (
          <img
            src={previewImage}
            className="absolute inset-0 w-full h-full object-contain"
            alt="Preview"
          />
        )}

        {/* VIDEO */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className={`absolute inset-0 w-full h-full object-cover ${
            isCameraOn && !previewImage ? "opacity-100" : "opacity-0"
          }`}
        />

        {/* PLACEHOLDER */}
        {!isCameraOn && !previewImage && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-white/60">
            <ScanLine size={48} />
            <span className="text-sm mt-2">
              Camera preview will appear here
            </span>
          </div>
        )}

        {/* GUIDE FRAME (TIDAK UNTUK CROP) */}
        {isCameraOn && !previewImage && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">

            <div
              className="
                relative
                w-[85%]
                max-w-[500px]
                aspect-[1.585/1]
                rounded-xl
                border-2 border-green-500
              "
              style={{
                boxShadow: "0 0 0 9999px rgba(0,0,0,0.55)"
              }}
            />

          </div>
        )}

        {/* LOADING */}
        {loading && (
          <div className="absolute inset-0 bg-black/70 flex items-center justify-center">
            <Loader className="animate-spin text-white" />
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 text-sm text-red-600 bg-red-50 p-2 rounded">
          {error}
        </div>
      )}

      {!previewImage && (
        <div className="flex gap-3 mt-4">
          <button
            onClick={startCamera}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg"
          >
            <Camera size={18} className="inline mr-2" />
            Start Camera
          </button>

          <label className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg text-center cursor-pointer">
            <Upload size={18} className="inline mr-2" />
            Upload
            <input type="file" accept="image/*" hidden onChange={handleUpload} />
          </label>
        </div>
      )}

      {isCameraOn && !previewImage && (
        <button
          onClick={capturePhoto}
          className="w-full mt-3 bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg"
        >
          Capture
        </button>
      )}

      {previewImage && (
        <>
          <button
            onClick={sendToBackend}
            className="w-full mt-3 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg"
          >
            Process Document
          </button>

          <button
            onClick={reset}
            className="w-full mt-2 bg-gray-500 hover:bg-gray-600 text-white py-2 rounded-lg"
          >
            Retake
          </button>
        </>
      )}

      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
};

export default CameraCapture;
