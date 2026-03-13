import cv2
import numpy as np
from PIL import Image
from transformers import pipeline


# ------------------------------------------------
# MODEL SETUP
# ------------------------------------------------

_pipe = None


def _load_pipeline():
    global _pipe
    if _pipe is not None:
        return _pipe

    # Pretrained deepfake detector fine-tuned on FaceForensics++
    _pipe = pipeline(
        "image-classification",
        model="dima806/deepfake_vs_real_image_detection",
        device=-1  # CPU; change to 0 if you have GPU
    )
    return _pipe


def _extract_face_crops(frame_bgr):
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )

    crops = []
    for (x, y, w, h) in faces:
        pad = int(0.2 * w)
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(frame_bgr.shape[1], x + w + pad)
        y2 = min(frame_bgr.shape[0], y + h + pad)
        crop_rgb = cv2.cvtColor(frame_bgr[y1:y2, x1:x2], cv2.COLOR_BGR2RGB)
        crops.append(Image.fromarray(crop_rgb))

    return crops


def detect_deepfake(video_path, sample_frames=20, confidence_threshold=0.65):
    """
    Detect deepfake content using a pretrained HuggingFace model
    fine-tuned on real vs fake face classification.
    """

    try:
        pipe = _load_pipeline()
    except Exception as e:
        return _empty_result(f"Could not load deepfake model: {str(e)}")

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return _empty_result("Could not open video file.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames == 0:
        cap.release()
        return _empty_result("Video has no frames.")

    sample_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)

    fake_scores = []
    faces_analyzed = 0
    flagged_frames = []
    face_crops_display = []

    for frame_idx in sample_indices:

        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
        ret, frame = cap.read()

        if not ret:
            continue

        crops = _extract_face_crops(frame)

        if not crops:
            continue

        for face_pil in crops:

            try:
                results = pipe(face_pil)

                fake_prob = 0.0
                for r in results:
                    label = r["label"].lower()
                    if "fake" in label or "deepfake" in label or "artificial" in label:
                        fake_prob = r["score"]
                        break

                faces_analyzed += 1
                fake_scores.append(fake_prob)

                if fake_prob >= confidence_threshold:
                    flagged_frames.append(int(frame_idx))
                    face_crops_display.append(np.array(face_pil))

            except Exception:
                continue

    cap.release()

    if not fake_scores:
        return _empty_result(
            "No faces detected in sampled frames. "
            "Deepfake analysis requires visible faces in the footage."
        )

    avg_fake_prob = float(np.mean(fake_scores))
    is_deepfake = avg_fake_prob >= confidence_threshold

    if avg_fake_prob >= 0.80:
        verdict = "Strong indicators of synthetic or deepfake content detected."
    elif avg_fake_prob >= 0.65:
        verdict = "Moderate indicators of deepfake manipulation detected. Manual review recommended."
    elif avg_fake_prob >= 0.40:
        verdict = "Low-confidence anomalies detected. Evidence is inconclusive."
    else:
        verdict = "No deepfake indicators detected. Faces appear authentic."

    return {
        "is_deepfake": is_deepfake,
        "confidence": round(avg_fake_prob * 100, 1),
        "faces_analyzed": faces_analyzed,
        "flagged_frames": flagged_frames,
        "face_crops": face_crops_display[:4],
        "verdict": verdict,
        "error": None
    }


def _empty_result(error_msg):
    return {
        "is_deepfake": False,
        "confidence": 0.0,
        "faces_analyzed": 0,
        "flagged_frames": [],
        "face_crops": [],
        "verdict": error_msg,
        "error": error_msg
    }