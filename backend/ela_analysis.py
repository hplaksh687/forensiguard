import cv2
import numpy as np
from PIL import Image, ImageEnhance
import io
from dataclasses import dataclass, field
from typing import List


@dataclass
class ELAResult:
    flagged_frames: List[int] = field(default_factory=list)
    ela_images: List[np.ndarray] = field(default_factory=list)
    original_images: List[np.ndarray] = field(default_factory=list)
    max_ela_scores: List[float] = field(default_factory=list)
    suspicious_regions: List[str] = field(default_factory=list)
    error: str = None


def _compute_ela(pil_image: Image.Image, quality: int = 95) -> tuple:
    """
    Compute Error Level Analysis for a single PIL image.
    Returns (ela_array, max_score, mean_score)
    """
    # Save at target quality into buffer
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    recompressed = Image.open(buffer).convert("RGB")

    # Compute absolute difference
    orig_arr = np.array(pil_image.convert("RGB"), dtype=np.float32)
    recomp_arr = np.array(recompressed, dtype=np.float32)

    ela_arr = np.abs(orig_arr - recomp_arr)

    # Amplify for visibility (scale to 0-255)
    scale = 255.0 / (ela_arr.max() + 1e-6) * 10
    ela_visual = np.clip(ela_arr * scale, 0, 255).astype(np.uint8)

    max_score = float(ela_arr.max())
    mean_score = float(ela_arr.mean())

    return ela_visual, max_score, mean_score


def analyze_ela(video_path: str, sample_frames: int = 8, threshold: float = 12.0) -> ELAResult:
    """
    Run ELA on sampled frames from a video to detect compression anomalies
    indicating possible tampering or spliced content.

    Args:
        video_path: path to video file
        sample_frames: how many frames to sample
        threshold: mean ELA score above this flags the frame as suspicious

    Returns:
        ELAResult dataclass
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return ELAResult(error="Could not open video file for ELA analysis.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames < 2:
        cap.release()
        return ELAResult(error="Video too short for ELA analysis.")

    sample_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)

    flagged_frames = []
    ela_images = []
    original_images = []
    max_scores = []
    suspicious_regions = []

    for frame_idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
        ret, frame = cap.read()

        if not ret:
            continue

        # Convert BGR → RGB PIL
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)

        # Resize for faster processing (max 640px wide)
        w, h = pil_img.size
        if w > 640:
            scale = 640 / w
            pil_img = pil_img.resize((640, int(h * scale)), Image.LANCZOS)
            frame_rgb = np.array(pil_img)

        try:
            ela_visual, max_score, mean_score = _compute_ela(pil_img)
        except Exception:
            continue

        max_scores.append(max_score)

        if mean_score > threshold:
            flagged_frames.append(int(frame_idx))
            ela_images.append(ela_visual)
            original_images.append(frame_rgb)

            # Identify which region has highest ELA activity
            h_img, w_img = ela_visual.shape[:2]
            ela_gray = cv2.cvtColor(ela_visual, cv2.COLOR_RGB2GRAY)

            # Divide into 3x3 grid, find hottest region
            grid_scores = []
            for row in range(3):
                for col in range(3):
                    r0, r1 = row * h_img // 3, (row + 1) * h_img // 3
                    c0, c1 = col * w_img // 3, (col + 1) * w_img // 3
                    grid_scores.append(ela_gray[r0:r1, c0:c1].mean())

            hottest = int(np.argmax(grid_scores))
            region_names = [
                "top-left", "top-center", "top-right",
                "mid-left", "center", "mid-right",
                "bottom-left", "bottom-center", "bottom-right"
            ]
            suspicious_regions.append(
                f"Frame #{int(frame_idx)}: highest anomaly in {region_names[hottest]} region "
                f"(ELA score: {mean_score:.1f})"
            )

    cap.release()

    return ELAResult(
        flagged_frames=flagged_frames,
        ela_images=ela_images[:4],
        original_images=original_images[:4],
        max_ela_scores=max_scores,
        suspicious_regions=suspicious_regions[:4],
        error=None
    )