# 🛡️ ForensiGuard
### Voice & CCTV Forensic Authentication System

> **CyberThon 26 — Problem Statement 14**  
> Detects tampering, deepfakes, synthetic voice, and metadata manipulation in CCTV footage and audio recordings.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🔍 What is ForensiGuard?

Criminal investigations increasingly rely on CCTV footage and voice recordings as evidence — but these files can be tampered with, deepfaked, or edited. ForensiGuard is an automated forensic analysis tool that verifies the authenticity of multimedia evidence using multiple detection techniques and generates a professional forensic report.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎵 **Audio Splicing Detection** | Detects spectral discontinuities indicating cut-and-splice edits |
| 🗑️ **Audio Deletion Detection** | Identifies suspicious silence regions from content removal |
| 🎤 **Synthetic Voice Detection** | Detects AI-cloned or TTS-generated voice using pitch & spectral analysis |
| 🖼️ **Deepfake Detection** | ML-based face analysis using a model fine-tuned on FaceForensics++ |
| 📊 **ELA Analysis** | Error Level Analysis detects frames saved at different compression levels |
| 🔄 **Frame Duplication** | Detects looped or frozen frames indicating video manipulation |
| 🗂️ **Metadata Forensics** | Detects FPS spoofing, codec anomalies, and editing tool traces via ffprobe |
| 🗜️ **Recompression Analysis** | Identifies re-encoded video using inter-frame variance patterns |
| 🔐 **SHA-256 Integrity Hash** | Tamper-evident cryptographic fingerprint of evidence files |
| 📋 **Chain of Custody Log** | Append-only audit trail of all analyses with timestamps and case IDs |
| 📄 **AI Forensic Report** | LLM-generated professional forensic investigation report (PDF export) |
| 📈 **Authenticity Score** | Weighted 0–100 score with per-module penalty breakdown |

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- ffprobe (install via `brew install ffmpeg` or `apt install ffmpeg`)
- Ollama (optional — for AI report generation): https://ollama.ai

### Install dependencies

```bash
git clone https://github.com/hplaksh687/Forensiguard.git
cd Forensiguard
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 📁 Project Structure

```
Forensiguard/
├── app.py                        # Main Streamlit application
├── requirements.txt
├── backend/
│   ├── audio_analysis.py         # Audio splicing, insertion, deletion, synthetic voice
│   ├── deepfake_detection.py     # ML deepfake face detection
│   ├── ela_analysis.py           # Error Level Analysis on video frames
│   ├── frame_analysis.py         # Frame duplication detection
│   ├── fingerprint.py            # Video metadata fingerprinting
│   ├── metadata_analysis.py      # ffprobe metadata forensics
│   ├── recompression_analysis.py # Recompression detection
│   ├── hash_analysis.py          # SHA-256 evidence hash
│   ├── file_screening.py         # MIME type & multi-extension detection
│   ├── auth_score.py             # Authenticity scoring engine
│   ├── custody_log.py            # Chain of custody logger
│   └── forensic_llm.py           # AI report generation + PDF export
```

---

## 🧠 How It Works

1. **Upload** a video (MP4, AVI, MOV) or audio file (WAV, MP3, M4A)
2. **ForensiGuard runs** 8+ forensic analysis modules in parallel
3. **Results are aggregated** into a weighted authenticity score (0–100)
4. **A verdict is issued** — AUTHENTIC / INCONCLUSIVE / TAMPERED
5. **Export** a PDF forensic report and chain of custody log

---

## 📊 Scoring System

| Score | Verdict | Meaning |
|---|---|---|
| 80–100 | ✅ AUTHENTIC | No significant anomalies |
| 50–79 | ⚠️ INCONCLUSIVE | Anomalies detected, manual review recommended |
| 0–49 | ❌ TAMPERED | Strong indicators of manipulation |

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit + custom CSS (dark forensic theme)
- **Audio Analysis**: librosa, numpy
- **Video Analysis**: OpenCV, PIL
- **Deepfake Detection**: HuggingFace Transformers (`dima806/deepfake_vs_real_image_detection`)
- **Metadata Extraction**: ffprobe (subprocess)
- **Report Generation**: Ollama (llama3) with ReportLab PDF
- **Visualisation**: Plotly (waveform, spectrogram, score chart)

---

## Live Demo

Try the deployed application here:

https://your-app-name.streamlit.app

---

## 👥 Team

Built for **CyberThon 26** — Cybersecurity Hackathon  
Problem Statement 14: Voice & CCTV Forensic Authentication System
Team Name - Three Musketeers
Team Members - Laksh H P, Rehan Riyaz and Shanaya Ray
  
