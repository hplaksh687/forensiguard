def calculate_authenticity_score(fingerprint, metadata_issues=None, recompressed=False, duplicates=None):
    """
    Authenticity scoring with calibrated penalties.

    Design principles:
    - Real videos should score 75-100 (minor false positives are expected)
    - Tampered videos should score 0-50
    - Suspicious/inconclusive videos should score 50-74
    - Penalties are only applied for STRONG indicators, not normal codec behaviour
    """

    score = 100
    issues = []

    # ── FINGERPRINT CHECKS ──
    # Only penalise genuinely broken fingerprints
    if fingerprint["fps"] <= 0:
        score -= 20
        issues.append("Invalid frame rate — file may be corrupt")

    if fingerprint["frame_count"] < 10:
        score -= 15
        issues.append("Video too short for reliable analysis")

    # ── METADATA ANOMALIES ──
    # Filter out low-signal noise before scoring
    if metadata_issues:
        IGNORED_PATTERNS = [
            "re-encoded using editing tool",   # too common on real videos
            "unusually low bitrate",           # phones and CCTV compress heavily
            "low average bitrate",             # same reason
            "missing codec profile",           # often stripped by cameras
        ]

        strong_issues = []
        weak_issues = []

        for issue in metadata_issues:
            is_weak = any(p.lower() in issue.lower() for p in IGNORED_PATTERNS)
            if is_weak:
                weak_issues.append(issue)
            else:
                strong_issues.append(issue)

        # Strong issues (frame rate mismatch, unusual codec) — meaningful penalty
        if strong_issues:
            penalty = min(len(strong_issues) * 12, 25)
            score -= penalty
            issues.extend(strong_issues)

        # Weak issues — just note them, tiny penalty
        if weak_issues:
            penalty = min(len(weak_issues) * 3, 10)
            score -= penalty
            issues.extend(weak_issues)

    # ── RECOMPRESSION ──
    # Most real-world videos have been re-encoded (phones, WhatsApp, CCTV DVR)
    # Only penalise if ALSO combined with other issues, or penalise lightly alone
    if recompressed:
        if issues:
            # Combined with other anomalies — more suspicious
            score -= 15
            issues.append("Recompression detected — combined with other anomalies, suggests editing")
        else:
            # Alone — common in legitimate footage, light penalty
            score -= 8
            issues.append("Recompression detected — may indicate re-encoding (common in CCTV systems)")

    # ── FRAME DUPLICATION ──
    # Real CCTV naturally has near-duplicate frames at low frame rates
    # Only penalise heavy or suspicious duplication
    if duplicates:
        if len(duplicates) > 30:
            score -= 25
            issues.append(f"Severe frame duplication: {len(duplicates)} frames — strong tampering indicator")
        elif len(duplicates) > 15:
            score -= 15
            issues.append(f"High frame duplication: {len(duplicates)} frames — possible loop or freeze")
        elif len(duplicates) > 5:
            score -= 8
            issues.append(f"Moderate frame duplication: {len(duplicates)} frames")
        else:
            # 1-5 duplicate frames — totally normal, no penalty
            issues.append(f"Minor frame duplication: {len(duplicates)} frames (within normal range)")

    score = max(0, score)

    return score, issues