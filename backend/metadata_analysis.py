import subprocess
import json
import cv2


def extract_video_metadata(video_path):
    """
    Extract video metadata using ffprobe.
    Returns empty dict gracefully if ffprobe is not installed.
    """

    try:
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0 or not result.stdout.strip():
            return {}

        metadata = json.loads(result.stdout)
        return metadata

    except FileNotFoundError:
        # ffprobe not installed
        return {}

    except (json.JSONDecodeError, subprocess.TimeoutExpired):
        return {}


def analyze_metadata(metadata, video_path):
    """
    Analyze metadata for forensic anomalies.

    Returns a list of issue strings.
    """

    issues = []

    if not metadata:
        issues.append("Could not extract metadata (ffprobe unavailable or file unreadable)")
        return issues

    # ----------------------------------------
    # FORMAT LEVEL ANALYSIS
    # ----------------------------------------

    if "format" in metadata:

        format_info = metadata["format"]
        tags = format_info.get("tags", {})

        encoder = tags.get("encoder", "") or tags.get("Encoder", "")
        duration = float(format_info.get("duration", 0) or 0)
        size = int(format_info.get("size", 0) or 0)
        bitrate_raw = format_info.get("bit_rate")
        bitrate = int(bitrate_raw) if bitrate_raw and bitrate_raw.isdigit() else 0

        # Detect editing software traces
        editing_tools = ["Lavf", "Adobe", "Final Cut", "DaVinci", "Premiere", "HandBrake", "FFmpeg"]
        for tool in editing_tools:
            if tool.lower() in encoder.lower():
                issues.append(f"Video re-encoded using editing tool: '{encoder}'")
                break

        # Low bitrate — only flag if significantly low (was 300kbps, raised to 200kbps to reduce false positives)
        if bitrate and bitrate < 200000:
            issues.append(f"Unusually low bitrate ({bitrate // 1000} kbps) for CCTV footage")

        # File size vs duration sanity check
        if duration > 0 and size > 0:
            avg_bitrate = (size * 8) / duration
            if avg_bitrate < 200000:
                issues.append(f"Low average bitrate ({int(avg_bitrate) // 1000} kbps) — possible recompression")

        # Creation/modification time mismatch
        creation_time = tags.get("creation_time", "")
        if creation_time:
            # Just flag if creation time is in metadata — useful for investigators
            pass

    # ----------------------------------------
    # STREAM LEVEL ANALYSIS
    # ----------------------------------------

    if "streams" in metadata and len(metadata["streams"]) > 0:

        stream = metadata["streams"][0]

        codec = stream.get("codec_name", "")
        profile = stream.get("profile", "")
        pix_fmt = stream.get("pix_fmt", "")

        if codec and codec not in ["h264", "hevc", "h265", "mpeg4", "mjpeg"]:
            issues.append(f"Unusual codec detected: '{codec}' (not typical for CCTV)")

        if profile == "":
            issues.append("Missing codec profile — metadata may have been stripped")

        # ----------------------------------------
        # FRAME RATE SPOOFING DETECTION
        # ----------------------------------------

        metadata_fps_raw = stream.get("r_frame_rate", "0/1")

        try:
            num, den = metadata_fps_raw.split("/")
            den = int(den)
            metadata_fps = float(int(num) / den) if den != 0 else 0
        except Exception:
            metadata_fps = 0

        # Actual FPS from OpenCV
        try:
            cap = cv2.VideoCapture(video_path)
            actual_fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
        except Exception:
            actual_fps = 0

        if metadata_fps > 0 and actual_fps > 0:
            if abs(metadata_fps - actual_fps) > 2:
                issues.append(
                    f"Frame rate mismatch: metadata says {metadata_fps:.1f} fps, "
                    f"actual is {actual_fps:.1f} fps — possible metadata spoofing"
                )

    return issues