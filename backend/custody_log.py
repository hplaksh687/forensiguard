import json
import datetime
import os
from typing import List, Optional


# Always store the log in the project root, regardless of where this module lives
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR) if os.path.basename(_THIS_DIR) == "backend" else _THIS_DIR
CUSTODY_LOG_FILE = os.path.join(_PROJECT_ROOT, "custody_log.json")


def _load_log() -> list:
    if not os.path.exists(CUSTODY_LOG_FILE):
        return []
    try:
        with open(CUSTODY_LOG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def append_custody_entry(
    filename: str,
    sha256: str,
    file_type: str,
    score: int,
    findings: List[str],
    analysis_time_seconds: float,
    is_tampered: bool
) -> dict:
    """
    Append a new entry to the chain of custody log.
    Returns the entry that was written.
    """
    entry = {
        "id": f"FR-{sha256[:8].upper()}",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "filename": filename,
        "sha256": sha256,
        "file_type": file_type,
        "authenticity_score": score,
        "verdict": (
            "TAMPERED" if score < 50 else
            "INCONCLUSIVE" if score < 80 else
            "AUTHENTIC"
        ),
        "is_tampered": is_tampered,
        "findings": findings,
        "analysis_duration_seconds": round(analysis_time_seconds, 2),
        "analyst": "ForensiGuard Automated System v1.0"
    }

    log = _load_log()
    log.append(entry)

    try:
        with open(CUSTODY_LOG_FILE, "w") as f:
            json.dump(log, f, indent=2)
    except Exception:
        pass  # don't crash the app if log write fails

    return entry


def get_custody_log() -> list:
    """Return full custody log, newest first."""
    log = _load_log()
    return list(reversed(log))


def export_custody_log_text(entries: Optional[list] = None) -> str:
    """Export custody log as formatted plain text for download."""
    if entries is None:
        entries = get_custody_log()

    lines = [
        "FORENSIGUARD — CHAIN OF CUSTODY LOG",
        "=" * 50,
        f"Exported: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"Total entries: {len(entries)}",
        "",
    ]

    for e in entries:
        lines += [
            f"Case ID   : {e.get('id', 'N/A')}",
            f"Timestamp : {e.get('timestamp', 'N/A')}",
            f"File      : {e.get('filename', 'N/A')}",
            f"SHA-256   : {e.get('sha256', 'N/A')}",
            f"Type      : {e.get('file_type', 'N/A')}",
            f"Score     : {e.get('authenticity_score', 'N/A')}/100",
            f"Verdict   : {e.get('verdict', 'N/A')}",
            f"Duration  : {e.get('analysis_duration_seconds', 'N/A')}s",
            "Findings  :",
        ]
        for finding in e.get("findings", []):
            lines.append(f"  - {finding}")
        lines += ["", "-" * 50, ""]

    return "\n".join(lines)