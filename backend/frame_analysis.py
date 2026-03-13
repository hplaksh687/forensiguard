import cv2
import numpy as np


def detect_frame_duplication(video_path, threshold=2.5, max_frames=500):
    """
    Detect duplicated or near-duplicate frames in a video.

    Args:
        video_path: path to the video file
        threshold: mean absolute diff below this = duplicate (was 1.0, now 2.5 to catch near-dupes)
        max_frames: cap frames processed to avoid hanging on long videos

    Returns:
        (duplicated_frame_indices, duplicated_frame_images, fps)
    """

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return [], [], 25.0

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Sample evenly if video is very long
    sample_step = max(1, total_frames // max_frames)

    prev_frame = None
    duplicated_frames = []
    frame_images = []
    frame_index = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        # Only process sampled frames for performance
        if frame_index % sample_step != 0:
            frame_index += 1
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is not None:

            diff = cv2.absdiff(prev_frame, gray)
            score = np.mean(diff)

            if score < threshold:
                duplicated_frames.append(frame_index)
                # Convert BGR to RGB for Streamlit display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_images.append(frame_rgb)

        prev_frame = gray
        frame_index += 1

    cap.release()

    return duplicated_frames, frame_images, fps