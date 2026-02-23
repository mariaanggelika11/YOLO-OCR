import React, { useState, useRef, useEffect } from "react";
import { Camera, Upload, Loader } from "lucide-react";
import { analyzeFrame, resetAnalyzer } from "../utils/FrameAnalyzer";

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

  // 🔥 NEW STATES
  const [warning, setWarning] = useState<string | null>(null);
  const [qualityScore, setQualityScore] = useState(0);
  const [isValidFrame, setIsValidFrame] = useState(false);
  const validTimerRef = useRef<number | null>(null);

  // =========================
  // START CAMERA
  // =========================
  const startCamera = async () => {
    setError("");

    try {
      // 🔥 Cek apakah browser support
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setError("Camera not supported on this device");
        return;
      }

      // 🔥 Coba akses kamera (akan trigger permission popup)
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
          aspectRatio: 1.585,
          width: { ideal: 1280 },
          height: { ideal: 800 },
        },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.setAttribute("playsinline", "true"); // 🔥 penting untuk Android
        await videoRef.current.play();
        setIsCameraOn(true);
      }

    } catch (err: any) {
      console.error("Camera error:", err);

      if (err.name === "NotAllowedError") {
        setError("Camera permission denied. Please allow camera access.");
      } else if (err.name === "NotFoundError") {
        setError("No camera device found.");
      } else {
        setError("Cannot access camera");
      }
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
  // REALTIME ANALYZER
  // =========================
  useEffect(() => {
    if (!isCameraOn || previewImage) return;

    const interval = setInterval(() => {
      runAnalyzer();
    }, 300);

    return () => clearInterval(interval);
  }, [isCameraOn, previewImage]);

  useEffect(() => {
    if (!previewImage) return;

    resetAnalyzer();

    const img = new Image();
    img.src = previewImage;

    img.onload = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      canvas.width = img.width;
      canvas.height = img.height;

      ctx.drawImage(img, 0, 0);

    const result = analyzeFrame(ctx,
        canvas.width,
        canvas.height,
        false
      );
      setWarning(result.warning);
      setQualityScore(result.score);
      setIsValidFrame(result.isValid);
    };
  }, [previewImage]);

  const runAnalyzer = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) return;
    if (video.videoWidth === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.drawImage(video, 0, 0);

    const result = analyzeFrame(ctx, canvas.width, canvas.height);

    setWarning(result.warning);
    setQualityScore(result.score);
    setIsValidFrame(result.isValid);

    // AUTO CAPTURE after 2 seconds valid
    if (result.isValid) {
      if (!validTimerRef.current) {
        validTimerRef.current = Date.now();
      }

      if (Date.now() - validTimerRef.current > 1200) {
        capturePhoto();
        validTimerRef.current = null;
      }
    } else {
      validTimerRef.current = null;
    }
  };

  // =========================
  // CAPTURE
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
  // UPLOAD (ORIGINAL)
  // =========================
  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError("");
    resetAnalyzer();
    if (!e.target.files?.length) return;

    const reader = new FileReader();
    reader.onload = () => {
      setPreviewImage(reader.result as string);
    };
    reader.readAsDataURL(e.target.files[0]);
  };

  // =========================
  // SEND BACKEND (ORIGINAL)
  // =========================
  // const sendToBackend = async () => {
  //   if (!previewImage) return;

  //   setLoading(true);
  //   setError("");

  //   try {
  //     const blob = await (await fetch(previewImage)).blob();
  //     const formData = new FormData();
  //     formData.append("file", blob, "document.jpg");

  //     const res = await fetch(`${API_BASE_URL}/detect`, {
  //       method: "POST",
  //       body: formData,
  //     });

  //     const data = await res.json();
  //     if (!res.ok) throw new Error(data.detail);

  //     onExtractedData(data.parsed);
  //   } catch (err: any) {
  //     setError(err.message);
  //   }

  //   setLoading(false);
  // };

  const sendToBackend = async () => {
  if (!previewImage) return;

  setLoading(true);
  setError("");

  try {
    
    const base64Data = previewImage.split(",")[1];
    const byteCharacters = atob(base64Data);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += 1024) {
      const slice = byteCharacters.slice(offset, offset + 1024);

      const byteNumbers = new Array(slice.length);
      for (let i = 0; i < slice.length; i++) {
        byteNumbers[i] = slice.charCodeAt(i);
      }

      byteArrays.push(new Uint8Array(byteNumbers));
    }

    const blob = new Blob(byteArrays, { type: "image/jpeg" });

    console.log("Sending blob size:", blob.size);

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
    // Stop camera if running
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
    }

    // Reset analyzer internal state
    resetAnalyzer();

    // Reset UI states
    setPreviewImage(null);
    setWarning(null);
    setQualityScore(0);
    setIsValidFrame(false);
    setError("");

    // Reset timer
    validTimerRef.current = null;

    // Ensure camera state off
    setIsCameraOn(false);
  };

  return (
    <div className="bg-white p-6 rounded-2xl shadow-xl w-full max-w-lg flex flex-col gap-4">

      <h2 className="text-xl font-bold text-gray-800 flex items-center gap-3">
        <div className="bg-indigo-600 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold">
          1
        </div>
        Scan Document
      </h2>

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

            {(isCameraOn || previewImage) && (
              <>
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div
                    ref={frameRef}
                    className={`relative w-[90%] aspect-[1.585/1] rounded-xl ${
                      isValidFrame
                        ? "border-2 border-green-500"
                        : "border-2 border-red-500"
                    }`}
                    style={{
                      boxShadow: "0 0 0 9999px rgba(0,0,0,0.65)",
                    }}
                  />
                </div>

                {warning && (
                  <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-red-600 text-white px-4 py-2 rounded-lg text-sm animate-pulse">
                    {warning}
                  </div>
                )}
              </>
            )}
          </>
        )}

        {loading && (
          <div className="absolute inset-0 bg-black/70 flex items-center justify-center">
            <Loader className="animate-spin text-white" />
          </div>
        )}
      </div>

      {(isCameraOn || previewImage) && (
        <div className="text-center">
          <div className="text-sm font-semibold">
            Quality Score: {qualityScore}
          </div>
          <div className="w-full bg-gray-200 h-2 rounded">
            <div
              className={`h-2 rounded ${
                qualityScore > 75
                  ? "bg-green-500"
                  : qualityScore > 50
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
              style={{ width: `${qualityScore}%` }}
            />
          </div>
        </div>
      )}

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