import cv2

def extract_video_fingerprint(video_path):

    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    cap.release()

    fingerprint = {
        "fps": fps,
        "resolution": f"{int(width)}x{int(height)}",
        "frame_count": frame_count
    }

    return fingerprint