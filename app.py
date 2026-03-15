import streamlit as st
import time

# backend modules
from backend.file_screening import detect_multi_extension, verify_file_type
from backend.hash_analysis import generate_evidence_hash
from backend.fingerprint import extract_video_fingerprint
from backend.metadata_analysis import extract_video_metadata, analyze_metadata
from backend.recompression_analysis import detect_recompression
from backend.frame_analysis import detect_frame_duplication
from backend.auth_score import calculate_authenticity_score
from backend.forensic_llm import generate_forensic_report, generate_pdf_report
from backend.deepfake_detection import detect_deepfake
from backend.audio_analysis import analyze_audio
from backend.ela_analysis import analyze_ela
from backend.custody_log import append_custody_entry, get_custody_log, export_custody_log_text


st.set_page_config(
    page_title="ForensiGuard",
    page_icon="shield",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0a0e0a !important;
    font-family: 'Rajdhani', sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background-image:
        linear-gradient(rgba(0,255,100,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,255,100,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
}
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(0,255,100,0.4), transparent);
    animation: scan 4s linear infinite;
    z-index: 999;
    pointer-events: none;
}
@keyframes scan { 0% { top: 0; } 100% { top: 100vh; } }

.fg-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 24px;
    background: rgba(10,20,12,0.92);
    border-bottom: 1px solid rgba(0,255,100,0.15);
    backdrop-filter: blur(8px);
    margin-bottom: 2rem;
}
.fg-logo { display: flex; align-items: center; gap: 12px; }
.fg-logo-icon {
    width: 36px; height: 36px;
    border: 1px solid rgba(0,255,100,0.3); border-radius: 6px;
    background: rgba(0,255,100,0.06);
    display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.fg-logo-text h1 {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.2rem !important; font-weight: 700 !important;
    color: #e8f5e9 !important; margin: 0 !important; padding: 0 !important;
    border: none !important; letter-spacing: 0.08em;
}
.fg-logo-text p {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem; color: rgba(0,255,100,0.5);
    letter-spacing: 0.2em; text-transform: uppercase; margin: 0;
}
.fg-status {
    font-family: 'Share Tech Mono', monospace; font-size: 0.75rem;
    color: rgba(200,230,200,0.6); display: flex; align-items: center; gap: 8px;
}
.fg-status-dot {
    width: 7px; height: 7px; background: #00ff64;
    border-radius: 50%; display: inline-block; animation: pulse 2s infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

.fg-hero { text-align: center; padding: 3rem 1rem 2rem; }
.fg-hero-icon {
    width: 72px; height: 72px;
    border: 1px solid rgba(0,255,100,0.2); border-radius: 50%;
    background: rgba(0,255,100,0.04);
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 1.2rem; font-size: 2rem;
}
.fg-hero h2 {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.8rem !important; font-weight: 700 !important;
    color: #e8f5e9 !important; border: none !important; letter-spacing: 0.04em;
}
.fg-hero p { color: rgba(200,230,200,0.55); font-size: 0.9rem; max-width: 480px; margin: 0.5rem auto 1.2rem; line-height: 1.6; }
.fg-tags { display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap; }
.fg-tag { font-family: 'Share Tech Mono', monospace; font-size: 0.7rem; color: rgba(0,255,100,0.6); letter-spacing: 0.05em; }
.fg-tag::before { content: '> '; }

.fg-card-title {
    font-family: 'Share Tech Mono', monospace; font-size: 0.72rem;
    color: rgba(0,255,100,0.7); letter-spacing: 0.15em; text-transform: uppercase;
    margin-bottom: 1rem; display: flex; align-items: center; gap: 8px;
}
.fg-card-title::before { content: '>_'; color: rgba(0,255,100,0.4); }

.fg-score-high { color: #00ff64; font-size: 2.8rem; font-weight: 700; font-family: 'Rajdhani', sans-serif; }
.fg-score-mid  { color: #ffb300; font-size: 2.8rem; font-weight: 700; font-family: 'Rajdhani', sans-serif; }
.fg-score-low  { color: #ff3d3d; font-size: 2.8rem; font-weight: 700; font-family: 'Rajdhani', sans-serif; }

.fg-hash {
    font-family: 'Share Tech Mono', monospace; font-size: 0.7rem;
    color: rgba(0,255,100,0.7); background: rgba(0,255,100,0.04);
    border: 1px solid rgba(0,255,100,0.12); border-left: 3px solid rgba(0,255,100,0.4);
    padding: 10px 14px; border-radius: 4px; word-break: break-all; letter-spacing: 0.05em;
}
.fg-timeline-item {
    font-family: 'Share Tech Mono', monospace; font-size: 0.75rem;
    color: rgba(200,230,200,0.8); background: rgba(255,61,61,0.05);
    border-left: 2px solid rgba(255,61,61,0.5);
    padding: 6px 12px; margin: 3px 0; border-radius: 0 4px 4px 0;
}
.fg-report {
    font-family: 'Share Tech Mono', monospace; font-size: 0.78rem;
    line-height: 1.8; color: rgba(200,230,200,0.8);
    background: rgba(0,0,0,0.4); border: 1px solid rgba(0,255,100,0.1);
    border-radius: 6px; padding: 1.5rem;
}

[data-testid="stFileUploader"] {
    background: rgba(0,255,100,0.02) !important;
    border: 1px dashed rgba(0,255,100,0.2) !important;
    border-radius: 8px !important; padding: 1rem !important;
}
.stButton > button {
    background: transparent !important; border: 1px solid rgba(0,255,100,0.3) !important;
    color: rgba(0,255,100,0.8) !important; font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.75rem !important; letter-spacing: 0.1em !important;
    border-radius: 4px !important; transition: all 0.2s !important;
}
.stButton > button:hover { background: rgba(0,255,100,0.08) !important; border-color: rgba(0,255,100,0.6) !important; }
.stDownloadButton > button {
    background: transparent !important; border: 1px solid rgba(0,255,100,0.3) !important;
    color: rgba(0,255,100,0.8) !important; font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.72rem !important; letter-spacing: 0.08em !important; width: 100% !important;
}
.stProgress > div > div > div { background: linear-gradient(90deg, #00ff64, #00c853) !important; }
[data-testid="stMetricValue"] { color: #c8e6c9 !important; font-family: 'Rajdhani', sans-serif !important; font-size: 1.3rem !important; }
[data-testid="stMetricLabel"] { color: rgba(0,255,100,0.5) !important; font-family: 'Share Tech Mono', monospace !important; font-size: 0.65rem !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; }
[data-testid="stMetric"] { background: rgba(0,255,100,0.03) !important; border: 1px solid rgba(0,255,100,0.1) !important; border-radius: 6px !important; padding: 10px 14px !important; }
.stMarkdown p { color: rgba(200,230,200,0.7) !important; font-family: 'Rajdhani', sans-serif !important; }
h1,h2,h3 { color: #c8e6c9 !important; font-family: 'Rajdhani', sans-serif !important; border: none !important; }
.stCaption { font-family: 'Share Tech Mono', monospace !important; color: rgba(0,255,100,0.4) !important; font-size: 0.65rem !important; letter-spacing: 0.08em !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] { display: none !important; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"] > .main { padding-top: 0 !important; }
[data-testid="stFileUploaderDropzone"] {
    background: rgba(0,255,100,0.02) !important;
    border: 1px dashed rgba(0,255,100,0.25) !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)


# ── HEADER ──
st.markdown("""
<div class="fg-header">
  <div class="fg-logo">
    <div class="fg-logo-icon">&#128737;</div>
    <div class="fg-logo-text">
      <h1>ForensiGuard</h1>
      <p>Digital Forensic Analysis System</p>
    </div>
  </div>
  <div class="fg-status">
    <span class="fg-status-dot"></span>
    System Active &nbsp;&nbsp; v1.0.0
  </div>
</div>
""", unsafe_allow_html=True)


# ── FILE UPLOAD ──
uploaded_file = st.file_uploader(
    "Drop evidence files here — Supports MP4, AVI, MOV, WAV, MP3 formats",
    type=["mp4", "avi", "mov", "wav", "mp3", "m4a"],
    label_visibility="collapsed"
)

if not uploaded_file:
    st.markdown("""
    <div class="fg-hero">
      <div class="fg-hero-icon">&#128196;</div>
      <h2>Evidence Authenticity Verification</h2>
      <p>Upload CCTV footage or audio recordings for comprehensive forensic analysis.
      Detect tampering, synthetic media, and metadata manipulation.</p>
      <div class="fg-tags">
        <span class="fg-tag">Audio Splicing</span>
        <span class="fg-tag">Frame Duplication</span>
        <span class="fg-tag">Voice Cloning</span>
        <span class="fg-tag">Deepfake Detection</span>
        <span class="fg-tag">Metadata Spoofing</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── SAVE FILE ──
filename = uploaded_file.name
is_audio = uploaded_file.type.startswith("audio") or filename.lower().endswith((".wav", ".mp3", ".m4a"))
is_video = not is_audio

file_path = "temp_audio" if is_audio else "temp_video.mp4"
if is_audio:
    ext = filename.split(".")[-1]
    file_path = f"temp_audio.{ext}"

with open(file_path, "wb") as f:
    f.write(uploaded_file.read())

st.success(f"Evidence file '{filename}' received. Initiating forensic pipeline...")


# ── RUN ANALYSIS ──
_t_start = time.time()
with st.spinner("Processing — please wait..."):

    evidence_hash = generate_evidence_hash(file_path)
    multi_ext = detect_multi_extension(filename)
    file_type = verify_file_type(file_path)

    audio_result = None
    ela_result = None
    fingerprint = {"fps": 0, "resolution": "N/A", "frame_count": 0}
    metadata_issues = []
    recompressed = False
    duplicates = []
    frame_images = []
    deepfake_result = {
        "error": "Deepfake detection requires video input.",
        "is_deepfake": False, "confidence": 0,
        "faces_analyzed": 0, "flagged_frames": [], "face_crops": []
    }
    score = 100
    score_issues = []

    if is_audio:
        audio_result = analyze_audio(file_path)
        if audio_result and not audio_result.error:
            if audio_result.splicing_detections:
                score -= min(30, len(audio_result.splicing_detections) * 5)
                score_issues.append(f"Audio splicing: {len(audio_result.splicing_detections)} event(s)")
            if audio_result.insertion_detections:
                score -= min(20, len(audio_result.insertion_detections) * 8)
                score_issues.append(f"Audio insertion: {len(audio_result.insertion_detections)} event(s)")
            if audio_result.deletion_detections:
                score -= min(20, len(audio_result.deletion_detections) * 8)
                score_issues.append(f"Audio deletion: {len(audio_result.deletion_detections)} event(s)")
            if audio_result.synthetic_voice_result and audio_result.synthetic_voice_result.is_synthetic:
                score -= 30
                score_issues.append(f"Synthetic voice detected ({audio_result.synthetic_voice_result.confidence}% confidence)")
            score = max(0, score)

    else:
        fingerprint = extract_video_fingerprint(file_path)
        metadata = extract_video_metadata(file_path)
        metadata_issues = analyze_metadata(metadata, file_path)
        recompressed = detect_recompression(file_path)

        frame_result = detect_frame_duplication(file_path)
        duplicates = frame_result[0] if len(frame_result) > 0 else []
        frame_images = frame_result[1] if len(frame_result) > 1 else []

        deepfake_result = detect_deepfake(file_path)
        ela_result = analyze_ela(file_path)

        score, score_issues = calculate_authenticity_score(
            fingerprint, metadata_issues, recompressed, duplicates
        )

        if deepfake_result["is_deepfake"]:
            penalty = min(30, int(deepfake_result["confidence"] * 0.3))
            score = max(0, score - penalty)
            score_issues.append(f"Deepfake probability: {deepfake_result['confidence']}%")

        if ela_result and not ela_result.error and ela_result.flagged_frames:
            ela_penalty = min(20, len(ela_result.flagged_frames) * 5)
            score = max(0, score - ela_penalty)
            score_issues.append(f"ELA compression anomalies: {len(ela_result.flagged_frames)} frame(s)")

_analysis_time = round(time.time() - _t_start, 2)

# ── CUSTODY LOG ──
_all_findings = list(score_issues)
append_custody_entry(
    filename=filename,
    sha256=evidence_hash,
    file_type=file_type,
    score=score,
    findings=_all_findings,
    analysis_time_seconds=_analysis_time,
    is_tampered=(score < 50)
)


# ── VERDICT BANNER ──
if score >= 80:
    _verdict_label = "✓ AUTHENTIC"
    _verdict_bg = "rgba(0,200,83,0.12)"
    _verdict_border = "rgba(0,200,83,0.5)"
    _verdict_color = "#00c853"
    _verdict_sub = "No significant tampering indicators detected."
elif score >= 50:
    _verdict_label = "⚠ INCONCLUSIVE"
    _verdict_bg = "rgba(255,179,0,0.12)"
    _verdict_border = "rgba(255,179,0,0.5)"
    _verdict_color = "#ffb300"
    _verdict_sub = "Anomalies detected. Manual forensic review recommended."
else:
    _verdict_label = "✗ TAMPERED"
    _verdict_bg = "rgba(255,61,61,0.12)"
    _verdict_border = "rgba(255,61,61,0.5)"
    _verdict_color = "#ff3d3d"
    _verdict_sub = "Strong indicators of tampering. Evidence integrity compromised."

st.markdown(f"""
<div style="
    background:{_verdict_bg};
    border:2px solid {_verdict_border};
    border-radius:10px;
    padding:18px 28px;
    margin:1.2rem 0 1.8rem;
    display:flex;
    align-items:center;
    justify-content:space-between;
    flex-wrap:wrap;
    gap:10px;
">
  <div>
    <div style="font-family:'Share Tech Mono',monospace;font-size:1.6rem;font-weight:700;color:{_verdict_color};letter-spacing:0.12em;">
      {_verdict_label}
    </div>
    <div style="font-family:'Rajdhani',sans-serif;font-size:0.95rem;color:rgba(200,230,200,0.7);margin-top:4px;">
      {_verdict_sub}
    </div>
  </div>
  <div style="text-align:right;font-family:'Share Tech Mono',monospace;font-size:0.75rem;color:rgba(200,230,200,0.45);">
    Case ID: FR-{evidence_hash[:8].upper()}<br>
    Analysis time: {_analysis_time}s<br>
    Score: {score}/100
  </div>
</div>
""", unsafe_allow_html=True)

# ── LAYOUT ──
left_col, right_col = st.columns([3, 2], gap="large")

with left_col:

    # File Screening
    st.markdown('<div class="fg-card-title">File Screening</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("MIME Type", file_type.split("/")[-1].upper() if "/" in file_type else file_type)
    with c2:
        st.metric("Multi-Extension", "DETECTED" if multi_ext else "None")
    with c3:
        st.metric("Filename", filename[:18] + "..." if len(filename) > 18 else filename)

    st.divider()

    # ── AUDIO SECTIONS ──
    if is_audio and audio_result:
        if audio_result.error:
            st.error(audio_result.error)
        else:
            # Audio Fingerprint
            st.markdown('<div class="fg-card-title">Audio Fingerprint</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Duration", f"{audio_result.duration:.1f}s")
            with c2:
                st.metric("Sample Rate", f"{audio_result.sample_rate} Hz")

            st.divider()

            # Splicing
            st.markdown('<div class="fg-card-title">Audio Splicing Detection</div>', unsafe_allow_html=True)
            if audio_result.splicing_detections:
                st.warning(f"{len(audio_result.splicing_detections)} splicing event(s) detected.")
                for det in audio_result.splicing_detections[:5]:
                    severity_icon = {"low": "[ LOW ]", "medium": "[ MED ]", "high": "[ HIGH ]"}.get(det.severity, "")
                    st.markdown(
                        f'<div class="fg-timeline-item">{severity_icon} &nbsp; {det.timestamp}s — {det.description}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.success("No audio splicing detected.")

            st.divider()

            # Insertion
            st.markdown('<div class="fg-card-title">Audio Insertion Detection</div>', unsafe_allow_html=True)
            if audio_result.insertion_detections:
                st.warning(f"{len(audio_result.insertion_detections)} insertion event(s) detected.")
                for det in audio_result.insertion_detections[:5]:
                    st.markdown(
                        f'<div class="fg-timeline-item">{det.start_time}s – {det.end_time}s — {det.description}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.success("No audio insertion anomalies detected.")

            st.divider()

            # Deletion
            st.markdown('<div class="fg-card-title">Audio Deletion Detection</div>', unsafe_allow_html=True)
            if audio_result.deletion_detections:
                st.warning(f"{len(audio_result.deletion_detections)} deletion event(s) detected.")
                for det in audio_result.deletion_detections[:5]:
                    st.markdown(
                        f'<div class="fg-timeline-item">{det.timestamp}s — {det.description}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.success("No suspicious silence or deletion regions detected.")

            st.divider()

            # Synthetic Voice
            st.markdown('<div class="fg-card-title">Synthetic Voice Detection</div>', unsafe_allow_html=True)
            sv = audio_result.synthetic_voice_result
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Synthetic Confidence", f"{sv.confidence}%")
            with c2:
                st.metric("Pitch Variation", sv.pitch_variation)
            with c3:
                st.metric("Spectral Stability", f"{sv.spectral_stability}%")

            if sv.is_synthetic:
                st.error("Voice characteristics consistent with synthetic or cloned audio.")
            else:
                st.success("No synthetic voice indicators detected.")

            st.divider()

            # ── WAVEFORM + SPECTROGRAM ──
            st.markdown('<div class="fg-card-title">Audio Analysis</div>', unsafe_allow_html=True)

            import plotly.graph_objects as go
            import numpy as np

            waveform = audio_result.waveform_data
            duration = audio_result.duration

            if waveform:
                times = [i * duration / len(waveform) for i in range(len(waveform))]

                fig_wave = go.Figure()

                # Splicing highlight regions (red)
                for det in audio_result.splicing_detections:
                    fig_wave.add_vrect(
                        x0=max(0, det.timestamp - 0.2), x1=min(duration, det.timestamp + 0.2),
                        fillcolor="rgba(255,60,60,0.25)", line_width=0,
                        annotation_text="", layer="below"
                    )

                # Deletion highlight regions (blue)
                for det in audio_result.deletion_detections:
                    fig_wave.add_vrect(
                        x0=max(0, det.timestamp - 0.1), x1=min(duration, det.timestamp + det.silence_duration),
                        fillcolor="rgba(30,120,255,0.25)", line_width=0,
                        annotation_text="", layer="below"
                    )

                fig_wave.add_trace(go.Scatter(
                    x=times, y=waveform,
                    mode="lines",
                    line=dict(color="#00e676", width=1),
                    name="Waveform",
                    showlegend=False
                ))

                fig_wave.add_trace(go.Scatter(
                    x=[None], y=[None], mode="markers",
                    marker=dict(size=10, color="rgba(255,60,60,0.6)", symbol="square"),
                    name="Splicing"
                ))
                fig_wave.add_trace(go.Scatter(
                    x=[None], y=[None], mode="markers",
                    marker=dict(size=10, color="rgba(30,120,255,0.6)", symbol="square"),
                    name="Deletion"
                ))

                fig_wave.update_layout(
                    height=200,
                    margin=dict(l=0, r=0, t=4, b=24),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(5,15,8,0.9)",
                    xaxis=dict(
                        showgrid=False, zeroline=False, color="rgba(200,230,200,0.4)",
                        tickfont=dict(size=9), ticksuffix="s"
                    ),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    legend=dict(
                        orientation="h", x=1, xanchor="right", y=1.15,
                        font=dict(color="rgba(200,230,200,0.7)", size=10),
                        bgcolor="rgba(0,0,0,0)"
                    )
                )

                st.caption("WAVEFORM ANALYSIS")
                st.plotly_chart(fig_wave, use_container_width=True, config={"displayModeBar": False})

            # Spectrogram
            spec = audio_result.spectrogram_data
            if spec and len(spec) > 0:
                spec_array = np.array(spec, dtype=float)
                spec_t = spec_array.T
                spec_log = np.log1p(spec_t)
                p_low  = np.percentile(spec_log, 5)
                p_high = np.percentile(spec_log, 98)
                spec_norm = np.clip((spec_log - p_low) / (p_high - p_low + 1e-9), 0, 1)
                spec_norm = spec_norm[::-1, :]

                n_frames = spec_norm.shape[1]
                time_axis = np.linspace(0, duration, n_frames)

                fig_spec = go.Figure(go.Heatmap(
                    z=spec_norm,
                    x=time_axis,
                    colorscale=[
                        [0.0,  "rgb(0,0,30)"],
                        [0.25, "rgb(0,30,120)"],
                        [0.5,  "rgb(0,100,180)"],
                        [0.7,  "rgb(0,180,120)"],
                        [0.85, "rgb(200,200,0)"],
                        [1.0,  "rgb(255,80,0)"]
                    ],
                    showscale=False,
                    zmin=0, zmax=1
                ))

                fig_spec.update_layout(
                    height=180,
                    margin=dict(l=0, r=0, t=4, b=24),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(
                        showgrid=False, zeroline=False, color="rgba(200,230,200,0.4)",
                        tickfont=dict(size=9), ticksuffix="s"
                    ),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                )

                st.caption("SPECTROGRAM")
                st.plotly_chart(fig_spec, use_container_width=True, config={"displayModeBar": False})
    else:

        # Media Fingerprint
        st.markdown('<div class="fg-card-title">Media Fingerprint</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Frame Rate", f"{round(fingerprint['fps'], 2)} fps")
        with c2:
            st.metric("Resolution", fingerprint["resolution"])
        with c3:
            st.metric("Total Frames", int(fingerprint["frame_count"]))

        st.divider()

        # Evidence Hash
        st.markdown('<div class="fg-card-title">Evidence Integrity — SHA-256</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="fg-hash">{evidence_hash}</div>', unsafe_allow_html=True)

        st.divider()

        # Metadata
        st.markdown('<div class="fg-card-title">Metadata Integrity Analysis</div>', unsafe_allow_html=True)
        if metadata_issues:
            for issue in metadata_issues:
                st.warning(issue)
        else:
            st.success("No metadata anomalies detected.")

        st.divider()

        # Recompression
        st.markdown('<div class="fg-card-title">Recompression Analysis</div>', unsafe_allow_html=True)
        if recompressed:
            st.warning("Possible recompression detected. Video may have been re-encoded after editing.")
        else:
            st.success("No recompression anomalies detected.")

        st.divider()

        # Frame Duplication
        st.markdown('<div class="fg-card-title">Frame Tampering Detection</div>', unsafe_allow_html=True)
        if duplicates:
            st.warning(f"{len(duplicates)} duplicated frame(s) detected.")
            if frame_images:
                st.caption("Sample duplicated frames identified during analysis:")
                cols = st.columns(min(2, len(frame_images)))
                for i in range(min(4, len(frame_images))):
                    with cols[i % 2]:
                        st.image(frame_images[i], caption=f"Frame #{duplicates[i]}", use_container_width=True)
        else:
            st.success("No duplicated frames detected.")

        st.divider()

        # Deepfake Detection
        st.markdown('<div class="fg-card-title">Deepfake Detection</div>', unsafe_allow_html=True)
        if deepfake_result["error"]:
            st.info(deepfake_result["error"])
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Fake Probability", f"{deepfake_result['confidence']}%")
            with c2:
                st.metric("Faces Analyzed", deepfake_result["faces_analyzed"])
            with c3:
                st.metric("Flagged Frames", len(deepfake_result["flagged_frames"]))

            if deepfake_result["is_deepfake"]:
                st.error(deepfake_result["verdict"])
            elif deepfake_result["confidence"] >= 45:
                st.warning(deepfake_result["verdict"])
            else:
                st.success(deepfake_result["verdict"])

            if deepfake_result["face_crops"]:
                st.caption("Flagged face regions identified as potentially synthetic:")
                cols = st.columns(min(2, len(deepfake_result["face_crops"])))
                for i, crop in enumerate(deepfake_result["face_crops"]):
                    with cols[i % 2]:
                        st.image(crop, caption=f"Flagged Face — Frame #{deepfake_result['flagged_frames'][i]}", use_container_width=True)

        st.divider()

        # ELA Analysis
        st.markdown('<div class="fg-card-title">Compression Integrity — Error Level Analysis</div>', unsafe_allow_html=True)
        if ela_result and ela_result.error:
            st.info(ela_result.error)
        elif ela_result and ela_result.flagged_frames:
            st.warning(f"{len(ela_result.flagged_frames)} frame(s) show compression anomalies consistent with tampering.")
            for region_note in ela_result.suspicious_regions:
                st.markdown(
                    f'<div class="fg-timeline-item">{region_note}</div>',
                    unsafe_allow_html=True
                )
            if ela_result.ela_images:
                st.caption("ELA heatmaps — bright areas indicate regions saved at different compression levels (tampering indicator):")
                n = min(4, len(ela_result.ela_images))
                cols = st.columns(n)
                for i in range(n):
                    with cols[i]:
                        st.image(ela_result.original_images[i], caption=f"Original — Frame #{ela_result.flagged_frames[i]}", use_container_width=True)
                        st.image(ela_result.ela_images[i], caption="ELA heatmap", use_container_width=True)
        else:
            st.success("No ELA compression anomalies detected. Frames appear consistently encoded.")


with right_col:

    # Authenticity Score
    st.markdown('<div class="fg-card-title">Authenticity Score</div>', unsafe_allow_html=True)

    if score >= 90:
        score_class = "fg-score-high"
        verdict = "Evidence appears authentic."
        verdict_color = "success"
    elif score >= 70:
        score_class = "fg-score-mid"
        verdict = "Anomalies detected. Further review recommended."
        verdict_color = "warning"
    else:
        score_class = "fg-score-low"
        verdict = "High likelihood of tampering. Evidence integrity compromised."
        verdict_color = "error"

    st.markdown(f'<div class="{score_class}">{score} / 100</div>', unsafe_allow_html=True)
    st.progress(score / 100)

    if verdict_color == "success":
        st.success(verdict)
    elif verdict_color == "warning":
        st.warning(verdict)
    else:
        st.error(verdict)

    if score_issues:
        import plotly.graph_objects as go
        st.caption("Score breakdown — penalty contributions:")
        _labels = [s[:40] for s in score_issues]
        _penalties = []
        _remaining = 100 - score
        _per = _remaining / len(score_issues) if score_issues else 0
        for _ in score_issues:
            _penalties.append(round(_per, 1))

        _fig_score = go.Figure(go.Bar(
            x=_penalties,
            y=_labels,
            orientation="h",
            marker=dict(
                color=[f"rgba(255,{max(30, 100 - int(p*3))},61,0.75)" for p in _penalties]
            ),
            text=[f"-{p}pts" for p in _penalties],
            textposition="outside",
            textfont=dict(color="rgba(200,230,200,0.7)", size=10)
        ))
        _fig_score.update_layout(
            height=max(120, len(score_issues) * 36),
            margin=dict(l=0, r=60, t=4, b=4),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,15,8,0.8)",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(
                showgrid=False, zeroline=False,
                tickfont=dict(color="rgba(200,230,200,0.7)", size=10)
            )
        )
        st.plotly_chart(_fig_score, use_container_width=True, config={"displayModeBar": False})

    st.divider()

    # Forensic Timeline
    st.markdown('<div class="fg-card-title">Forensic Timeline</div>', unsafe_allow_html=True)
    fps = fingerprint["fps"] if fingerprint["fps"] > 0 else 25
    has_events = False

    if is_audio and audio_result and not audio_result.error:
        for det in audio_result.splicing_detections[:5]:
            has_events = True
            st.markdown(
                f'<div class="fg-timeline-item">{det.timestamp}s — Splicing detected</div>',
                unsafe_allow_html=True
            )
        for det in audio_result.deletion_detections[:3]:
            has_events = True
            st.markdown(
                f'<div class="fg-timeline-item">{det.timestamp}s — Silence/deletion detected</div>',
                unsafe_allow_html=True
            )

    if is_video:
        for frame_id in duplicates[:8]:
            has_events = True
            seconds = int(frame_id / fps)
            mins = seconds // 60
            secs = seconds % 60
            st.markdown(
                f'<div class="fg-timeline-item">{mins:02}:{secs:02} — Duplicated frame at index #{frame_id}</div>',
                unsafe_allow_html=True
            )
        for frame_id in deepfake_result["flagged_frames"][:5]:
            has_events = True
            seconds = int(frame_id / fps)
            mins = seconds // 60
            secs = seconds % 60
            st.markdown(
                f'<div class="fg-timeline-item">{mins:02}:{secs:02} — Deepfake face at frame #{frame_id}</div>',
                unsafe_allow_html=True
            )

    if not has_events:
        st.caption("No forensic timeline events to report.")


# ── AI REPORT ──
st.divider()
st.markdown('<div class="fg-card-title">AI Investigation Report</div>', unsafe_allow_html=True)

with st.spinner("Generating forensic report..."):
    report_text = generate_forensic_report(
        fingerprint, metadata_issues, recompressed,
        duplicates, score_issues, score
    )

st.markdown(f'<div class="fg-report">{report_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

st.divider()


# ── EXPORT ──
st.markdown('<div class="fg-card-title">Export Report</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    with st.spinner("Preparing PDF..."):
        pdf_path = generate_pdf_report(report_text, score=score, filename="forensic_report.pdf")
    if pdf_path:
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="DOWNLOAD FORENSIC REPORT (.PDF)",
                data=pdf_file,
                file_name=f"forensic_report_{filename.split('.')[0]}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

with col2:
    st.download_button(
        label="DOWNLOAD EVIDENCE HASH (.TXT)",
        data=f"File: {filename}\nSHA-256: {evidence_hash}\nAuthenticity Score: {score}/100\n",
        file_name=f"evidence_hash_{filename.split('.')[0]}.txt",
        mime="text/plain",
        use_container_width=True
    )

st.divider()

# ── CHAIN OF CUSTODY LOG ──
st.markdown('<div class="fg-card-title">Chain of Custody Log</div>', unsafe_allow_html=True)
st.caption("Tamper-evident audit trail of all analyses performed in this session.")

_custody_entries = get_custody_log()
if _custody_entries:
    for _entry in _custody_entries[:5]:
        _e_color = "#00c853" if _entry["verdict"] == "AUTHENTIC" else "#ffb300" if _entry["verdict"] == "INCONCLUSIVE" else "#ff3d3d"
        st.markdown(f"""
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;
            background:rgba(0,255,100,0.03);border:1px solid rgba(0,255,100,0.1);
            border-left:3px solid {_e_color};border-radius:0 6px 6px 0;
            padding:8px 14px;margin:4px 0;">
          <span style="color:{_e_color};font-weight:700;">{_entry['verdict']}</span>
          &nbsp;&nbsp;
          <span style="color:rgba(200,230,200,0.8);">{_entry['filename']}</span>
          &nbsp;|&nbsp;
          <span style="color:rgba(200,230,200,0.5);">Score: {_entry['authenticity_score']}/100</span>
          &nbsp;|&nbsp;
          <span style="color:rgba(200,230,200,0.4);">{_entry['timestamp']}</span>
          &nbsp;|&nbsp;
          <span style="color:rgba(200,230,200,0.35);">ID: {_entry['id']}</span>
        </div>
        """, unsafe_allow_html=True)

    st.download_button(
        label="DOWNLOAD CHAIN OF CUSTODY LOG (.TXT)",
        data=export_custody_log_text(_custody_entries),
        file_name="custody_log.txt",
        mime="text/plain",
    )
else:
    st.caption("No entries yet.")

# ── FOOTER ──
st.markdown("""
<div style="text-align:center; padding: 2rem 0 1rem; font-family: 'Share Tech Mono', monospace;
font-size: 0.65rem; color: rgba(0,255,100,0.25); letter-spacing: 0.1em;">
ForensiGuard &nbsp;|&nbsp; Cybersecurity Forensic Investigation Tool
</div>
""", unsafe_allow_html=True)