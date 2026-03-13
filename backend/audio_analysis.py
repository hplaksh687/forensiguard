import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple
import librosa


# ------------------------------------------------
# DATA CLASSES
# ------------------------------------------------

@dataclass
class SplicingDetection:
    timestamp: float
    severity: str  # 'low' | 'medium' | 'high'
    description: str
    spectral_difference: float


@dataclass
class InsertionDetection:
    start_time: float
    end_time: float
    severity: str
    description: str
    noise_variance: float


@dataclass
class DeletionDetection:
    timestamp: float
    severity: str
    description: str
    silence_duration: float


@dataclass
class SyntheticVoiceResult:
    is_synthetic: bool
    confidence: float       # 0–100
    pitch_variation: float
    spectral_stability: float
    mfcc_consistency: float


@dataclass
class AudioAnalysisResult:
    splicing_detections: List[SplicingDetection] = field(default_factory=list)
    insertion_detections: List[InsertionDetection] = field(default_factory=list)
    deletion_detections: List[DeletionDetection] = field(default_factory=list)
    synthetic_voice_result: SyntheticVoiceResult = None
    waveform_data: List[float] = field(default_factory=list)
    spectrogram_data: List[List[float]] = field(default_factory=list)
    duration: float = 0.0
    sample_rate: int = 22050
    error: str = None


# ------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------

def _compute_rms(data: np.ndarray, start: int, length: int) -> float:
    end = min(start + length, len(data))
    segment = data[start:end]
    if len(segment) == 0:
        return 0.0
    return float(np.sqrt(np.mean(segment ** 2)))


def _compute_zero_crossing_rate(data: np.ndarray, start: int, length: int) -> float:
    end = min(start + length, len(data))
    segment = data[start:end]
    if len(segment) < 2:
        return 0.0
    crossings = np.sum(
        ((segment[1:] >= 0) & (segment[:-1] < 0)) |
        ((segment[1:] < 0) & (segment[:-1] >= 0))
    )
    return float(crossings / len(segment))


def _compute_spectral_centroid(fft_mag: np.ndarray, sample_rate: int) -> float:
    bin_size = sample_rate / (len(fft_mag) * 2)
    freqs = np.arange(len(fft_mag)) * bin_size
    total = np.sum(fft_mag)
    if total == 0:
        return 0.0
    return float(np.sum(fft_mag * freqs) / total)


def _hanning_window(data: np.ndarray) -> np.ndarray:
    n = len(data)
    window = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n) / (n - 1))
    return data * window


# ------------------------------------------------
# MAIN ANALYSIS FUNCTION
# ------------------------------------------------

def analyze_audio(audio_path: str) -> AudioAnalysisResult:
    """
    Full forensic audio analysis — Python port of the JS Web Audio API implementation.

    Detects:
    - Audio splicing (spectral discontinuities)
    - Audio insertion (noise floor anomalies)
    - Audio deletion (suspicious silence regions)
    - Synthetic/cloned voice (pitch + spectral stability heuristics)

    Args:
        audio_path: path to audio file (WAV, MP3, etc.)

    Returns:
        AudioAnalysisResult dataclass
    """

    try:
        # Load audio with librosa (resamples to 22050 Hz by default)
        y, sr = librosa.load(audio_path, sr=None, mono=True)
    except Exception as e:
        return AudioAnalysisResult(error=f"Could not load audio file: {str(e)}")

    duration = float(len(y) / sr)

    # ----------------------------------------
    # WAVEFORM DATA (downsampled to 1000 points)
    # ----------------------------------------
    waveform_samples = 1000
    samples_per_point = max(1, len(y) // waveform_samples)
    waveform_data = []
    for i in range(waveform_samples):
        start = i * samples_per_point
        end = min(start + samples_per_point, len(y))
        waveform_data.append(float(np.max(np.abs(y[start:end]))))

    # ----------------------------------------
    # SPECTROGRAM DATA (200 frames, 128 bins)
    # ----------------------------------------
    hop_length = 128
    n_fft = 256
    stft = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    # Take first 200 frames, first 128 freq bins
    spec_frames = min(200, stft.shape[1])
    spectrogram_data = stft[:128, :spec_frames].T.tolist()

    # ----------------------------------------
    # SPECTRAL CENTROID PER FRAME (for splicing)
    # ----------------------------------------
    frame_size = int(sr * 0.1)  # 100ms frames
    centroids = []
    i = 0
    while i < len(y) - frame_size:
        frame = y[i:i + min(256, frame_size)]
        windowed = _hanning_window(frame)
        fft_mag = np.abs(np.fft.rfft(windowed))
        centroids.append(_compute_spectral_centroid(fft_mag, sr))
        i += frame_size

    # ----------------------------------------
    # SPLICING DETECTION
    # ----------------------------------------
    splicing_detections = []
    if len(centroids) > 1:
        avg_centroid = np.mean(centroids)
        threshold = avg_centroid * 0.5

        for i in range(1, len(centroids)):
            diff = abs(centroids[i] - centroids[i - 1])
            if diff > threshold:
                timestamp = round((i * frame_size) / sr, 1)
                if diff > threshold * 2:
                    severity = "high"
                elif diff > threshold * 1.5:
                    severity = "medium"
                else:
                    severity = "low"

                splicing_detections.append(SplicingDetection(
                    timestamp=timestamp,
                    severity=severity,
                    description=f"Spectral discontinuity detected at {timestamp}s (possible audio splicing)",
                    spectral_difference=round(diff)
                ))

    # ----------------------------------------
    # INSERTION DETECTION (noise floor)
    # ----------------------------------------
    insertion_detections = []
    noise_frame_size = int(sr * 0.5)  # 500ms
    rms_values = []
    i = 0
    while i < len(y) - noise_frame_size:
        rms_values.append(_compute_rms(y, i, noise_frame_size))
        i += noise_frame_size

    if len(rms_values) > 2:
        avg_rms = np.mean(rms_values)
        rms_std = np.std(rms_values)

        for i in range(1, len(rms_values) - 1):
            deviation = abs(rms_values[i] - avg_rms)
            if deviation > 2.5 * rms_std and rms_values[i] > avg_rms:
                start_time = round((i * noise_frame_size) / sr, 1)
                end_time = round(((i + 1) * noise_frame_size) / sr, 1)
                severity = "high" if deviation > 3.5 * rms_std else "medium"

                insertion_detections.append(InsertionDetection(
                    start_time=start_time,
                    end_time=end_time,
                    severity=severity,
                    description=f"Inconsistent acoustic pattern at {start_time}s–{end_time}s (possible audio insertion)",
                    noise_variance=round(rms_values[i] / avg_rms, 2)
                ))

    # ----------------------------------------
    # DELETION DETECTION (silence analysis)
    # ----------------------------------------
    deletion_detections = []
    silence_frame_size = int(sr * 0.05)  # 50ms
    avg_rms_val = float(np.sqrt(np.mean(y ** 2)))
    silence_threshold = avg_rms_val * 0.05
    silence_start = -1
    i = 0

    while i < len(y) - silence_frame_size:
        rms = _compute_rms(y, i, silence_frame_size)
        if rms < silence_threshold:
            if silence_start == -1:
                silence_start = i
        else:
            if silence_start != -1:
                silence_duration = (i - silence_start) / sr
                if 0.15 < silence_duration < 2.0:
                    zcr_before = (
                        _compute_zero_crossing_rate(y, silence_start - silence_frame_size, silence_frame_size)
                        if silence_start > silence_frame_size else 0
                    )
                    zcr_after = _compute_zero_crossing_rate(y, i, silence_frame_size)

                    if abs(zcr_before - zcr_after) > 0.1 or silence_duration > 0.5:
                        timestamp = round(silence_start / sr, 1)
                        severity = "high" if silence_duration > 1.0 else "medium" if silence_duration > 0.5 else "low"

                        deletion_detections.append(DeletionDetection(
                            timestamp=timestamp,
                            severity=severity,
                            description=f"Abrupt silence ({silence_duration:.2f}s) at {timestamp}s (possible audio deletion)",
                            silence_duration=round(silence_duration, 2)
                        ))
                silence_start = -1
        i += silence_frame_size

    # ----------------------------------------
    # SYNTHETIC VOICE DETECTION
    # ----------------------------------------
    pitch_frame_size = int(sr * 0.03)  # 30ms
    pitches = []
    max_analyze = min(len(y) - pitch_frame_size, sr * 10)
    i = 0

    while i < max_analyze:
        rms = _compute_rms(y, i, pitch_frame_size)
        if rms > silence_threshold * 2:
            # Autocorrelation pitch estimation
            segment = y[i:i + pitch_frame_size]
            min_lag = int(sr / 500)  # 500Hz max pitch
            max_lag = int(sr / 80)   # 80Hz min pitch
            max_lag = min(max_lag, pitch_frame_size - 1)

            if min_lag < max_lag:
                corr = np.correlate(segment, segment, mode='full')
                corr = corr[len(corr) // 2:]  # take positive lags
                lags = np.arange(min_lag, max_lag)
                if len(lags) > 0 and max_lag <= len(corr):
                    best_lag = lags[np.argmax(corr[min_lag:max_lag])]
                    if best_lag > 0:
                        pitches.append(sr / best_lag)
        i += pitch_frame_size

    if pitches:
        avg_pitch = np.mean(pitches)
        pitch_variation = float(np.std(pitches) / avg_pitch) if avg_pitch > 0 else 0
    else:
        pitch_variation = 0.0

    avg_sc = np.mean(centroids) if centroids else 1
    sc_variation = float(np.std(centroids) / avg_sc) if avg_sc > 0 else 0

    # Synthetic heuristic: low pitch variation + high spectral stability = likely synthetic
    synthetic_score = max(0.0, min(1.0,
        (1 - pitch_variation * 5) * 0.5 + (1 - sc_variation * 3) * 0.5
    ))

    synthetic_voice_result = SyntheticVoiceResult(
        is_synthetic=synthetic_score > 0.65,
        confidence=round(synthetic_score * 100, 1),
        pitch_variation=round(pitch_variation, 3),
        spectral_stability=round((1 - sc_variation) * 100, 1),
        mfcc_consistency=round((1 - pitch_variation) * 100, 1)
    )

    return AudioAnalysisResult(
        splicing_detections=splicing_detections[:10],
        insertion_detections=insertion_detections[:5],
        deletion_detections=deletion_detections[:5],
        synthetic_voice_result=synthetic_voice_result,
        waveform_data=waveform_data,
        spectrogram_data=spectrogram_data,
        duration=duration,
        sample_rate=sr,
        error=None
    )