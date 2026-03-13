import cv2
import numpy as np


def detect_recompression(video_path, sample_limit=200, std_threshold=20):
    """
    Detect if a video has been recompressed (re-encoded after editing).

    Uses variance of inter-frame differences. A recompressed video tends to
    have irregular variance patterns compared to original CCTV footage.

    Args:
        video_path: path to the video file
        sample_limit: max frames to sample (for performance on long videos)
        std_threshold: std deviation above this indicates recompression

    Returns:
        True if recompression likely detected, False otherwise
    """

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return False

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Sample evenly across video rather than reading all frames
    sample_step = max(1, total_frames // sample_limit)

    prev_frame = None
    variances = []
    frame_index = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        if frame_index % sample_step != 0:
            frame_index += 1
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is not None:
            diff = cv2.absdiff(prev_frame, gray)
            variance = np.var(diff)
            variances.append(variance)

        prev_frame = gray
        frame_index += 1

    cap.release()

    if len(variances) < 5:
        return False

    std_dev = np.std(variances)
    mean_var = np.mean(variances)

    # Coefficient of variation: normalized measure, more reliable than raw std
    # High CoV = highly irregular frame differences = likely recompressed
    if mean_var > 0:
        coeff_of_variation = std_dev / mean_var
        if coeff_of_variation > 1.5:
            return True

    # Fallback: raw std threshold
    if std_dev > std_threshold:
        return True

    return False