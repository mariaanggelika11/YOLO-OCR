export interface FrameAnalysisResult {
  warning: string | null;
  score: number;
  isValid: boolean;
}

let previousFrame: Uint8ClampedArray | null = null;

// ===============================
// RESET
// ===============================
export function resetAnalyzer() {
  previousFrame = null;
}

// ===============================
// MAIN ANALYZER (FINAL STABLE)
// ===============================
export function analyzeFrame(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  disableMotion: boolean = false
): FrameAnalysisResult {

  const frame = ctx.getImageData(0, 0, width, height);
  const data = frame.data;

  let brightness = 0;
  let sharpnessSum = 0;
  let edgeCount = 0;
  let motionScore = 0;

  // Sampling biar cepat & stabil
  const step = 6;
  let sampled = 0;

  // ==============================
  // BRIGHTNESS + SHARPNESS
  // ==============================
  for (let y = 2; y < height - 2; y += step) {
    for (let x = 2; x < width - 2; x += step) {

      const idx = (y * width + x) * 4;

      const r = data[idx];
      const g = data[idx + 1];
      const b = data[idx + 2];

      const gray = 0.299 * r + 0.587 * g + 0.114 * b;
      brightness += gray;

      // Laplacian blur detection (lebih akurat)
      const center = data[idx];
      const left = data[idx - 4];
      const right = data[idx + 4];
      const top = data[idx - width * 4];
      const bottom = data[idx + width * 4];

      const laplacian = Math.abs(4 * center - left - right - top - bottom);
      sharpnessSum += laplacian;

      if (laplacian > 40) edgeCount++;

      sampled++;
    }
  }

  brightness /= sampled;
  const sharpness = sharpnessSum / sampled;
  const edgeDensity = edgeCount / sampled;

  // ==============================
  // MOTION DETECTION (LESS SENSITIVE)
  // ==============================
  if (!disableMotion && previousFrame) {
    let diff = 0;

    for (let i = 0; i < data.length; i += 60) {
      diff += Math.abs(data[i] - previousFrame[i]);
    }

    motionScore = diff / (data.length / 60);
  }

  previousFrame = disableMotion ? null : data;

  // ==============================
  // QUALITY SCORE (BALANCED)
  // ==============================
  let score = 100;

  if (brightness < 45 || brightness > 245) score -= 10;
  if (sharpness < 18) score -= 25;
  if (edgeDensity < 0.01) score -= 15;
  if (!disableMotion && motionScore > 30) score -= 20;

  score = Math.max(0, score);

  // ==============================
  // VALIDATION LOGIC
  // ==============================

  if (!disableMotion && motionScore > 40) {
    return { warning: "Hold steady...", score, isValid: false };
  }

  if (brightness < 40) {
    return { warning: "Too dark", score, isValid: false };
  }

  if (brightness > 250) {
    return { warning: "Too bright", score, isValid: false };
  }

  if (sharpness < 15) {
    return { warning: "Slightly blurry", score, isValid: false };
  }

  if (edgeDensity < 0.008) {
    return { warning: "Adjust card position", score, isValid: false };
  }

  if (score < 50) {
    return { warning: "Adjust position", score, isValid: false };
  }

  return { warning: null, score, isValid: true };
}