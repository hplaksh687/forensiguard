import datetime
import ollama
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4


def generate_forensic_report(
    fingerprint,
    metadata_issues,
    recompressed,
    duplicates,
    security_flags,
    score=None
):
    """
    Generate an AI forensic investigation report using Ollama (llama3).
    Falls back to a structured rule-based report if Ollama is unavailable.

    Returns:
        report_text (str)
    """

    # Summarize duplicate count instead of dumping raw list
    duplicate_summary = (
        f"{len(duplicates)} duplicated frame(s) detected at indices: {duplicates[:5]}{'...' if len(duplicates) > 5 else ''}"
        if duplicates else "None"
    )

    score_line = f"\nAuthenticity Score: {score}/100" if score is not None else ""

    prompt = f"""You are a professional digital forensic analyst writing an official CCTV evidence investigation report.

Based on the findings below, write a concise and professional forensic report. Use formal language.
Structure the report with: Summary, Findings, Conclusion.

--- FORENSIC FINDINGS ---

Media Fingerprint:
- FPS: {fingerprint.get('fps', 'N/A')}
- Resolution: {fingerprint.get('resolution', 'N/A')}
- Frame Count: {fingerprint.get('frame_count', 'N/A')}
{score_line}

Metadata Issues:
{chr(10).join(f'- {i}' for i in metadata_issues) if metadata_issues else '- None detected'}

Recompression Detected: {'Yes — video may have been re-encoded after editing' if recompressed else 'No'}

Frame Duplication: {duplicate_summary}

Additional Security Flags:
{chr(10).join(f'- {f}' for f in security_flags) if security_flags else '- None'}

--- END OF FINDINGS ---

Write the report now:"""

    try:
        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )
        report_text = response["message"]["content"]

    except Exception as e:
        # Fallback: generate a structured report without LLM
        report_text = _generate_fallback_report(
            fingerprint, metadata_issues, recompressed, duplicates, security_flags, score
        )

    return report_text


def _generate_fallback_report(fingerprint, metadata_issues, recompressed, duplicates, security_flags, score):
    """
    Rule-based fallback report when Ollama is not available.
    """

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_issues = metadata_issues + security_flags
    if recompressed:
        all_issues.append("Recompression detected")
    if duplicates:
        all_issues.append(f"{len(duplicates)} duplicated frame(s) found")

    if score is None:
        score = 100 - (len(all_issues) * 10)
        score = max(0, min(100, score))

    verdict = (
        "The evidence appears authentic with no significant anomalies."
        if score >= 90 else
        "The evidence shows some anomalies that warrant further investigation."
        if score >= 70 else
        "The evidence shows strong indicators of tampering and is likely not authentic."
    )

    lines = [
        "FORENSIGUARD DIGITAL FORENSIC REPORT",
        f"Generated: {now}",
        "",
        "SUMMARY",
        "-------",
        f"This report presents the results of an automated forensic analysis of submitted CCTV footage.",
        f"Authenticity Score: {score}/100",
        "",
        "MEDIA FINGERPRINT",
        "-----------------",
        f"Resolution : {fingerprint.get('resolution', 'N/A')}",
        f"Frame Rate : {fingerprint.get('fps', 'N/A')} fps",
        f"Frame Count: {int(fingerprint.get('frame_count', 0))}",
        "",
        "FINDINGS",
        "--------",
    ]

    if all_issues:
        for issue in all_issues:
            lines.append(f"[!] {issue}")
    else:
        lines.append("[✓] No anomalies detected")

    lines += [
        "",
        "CONCLUSION",
        "----------",
        verdict,
        "",
        "--- End of Report ---"
    ]

    return "\n".join(lines)


def generate_pdf_report(report_text, score=None, filename="forensic_report.pdf"):
    """
    Generate a professionally formatted PDF forensic report.

    Args:
        report_text: the report body text
        score: optional authenticity score (0-100)
        filename: output PDF filename

    Returns:
        pdf_path (str)
    """

    pdf_path = filename
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ForensiTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "ForensiSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=4
    )

    section_style = ParagraphStyle(
        "ForensiSection",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#2b4099"),
        spaceBefore=14,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        "ForensiBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#2d3748")
    )

    story = []

    # Header
    story.append(Paragraph("🛡️ ForensiGuard", title_style))
    story.append(Paragraph("Digital Forensic Evidence Report", subtitle_style))
    story.append(Paragraph(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2b4099")))
    story.append(Spacer(1, 12))

    # Score badge if available
    if score is not None:
        score_color = (
            colors.HexColor("#48bb78") if score >= 90 else
            colors.HexColor("#ed8936") if score >= 70 else
            colors.HexColor("#fc8181")
        )
        score_data = [["Authenticity Score", f"{score} / 100"]]
        score_table = Table(score_data, colWidths=[2.5 * inch, 2 * inch])
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#2b4099")),
            ("BACKGROUND", (1, 0), (1, 0), score_color),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [None]),
            ("ROUNDEDCORNERS", [4]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 16))

    # Report body — split into sections by known headers
    current_section = None
    section_keywords = ["SUMMARY", "FINDINGS", "CONCLUSION", "MEDIA FINGERPRINT", "FORENSIC TIMELINE"]

    for line in report_text.split("\n"):
        line = line.strip()

        if not line:
            story.append(Spacer(1, 6))
            continue

        # Detect section headers
        is_section = any(line.upper().startswith(kw) for kw in section_keywords)
        is_dashes = set(line) <= {"-", "=", "_"} and len(line) > 3

        if is_dashes:
            continue

        if is_section or (line.isupper() and len(line) > 4):
            story.append(Paragraph(line.title(), section_style))
        elif line.startswith("[!]") or line.startswith("⚠"):
            story.append(Paragraph(f'<font color="#e53e3e">{line}</font>', body_style))
        elif line.startswith("[✓]") or line.startswith("✅"):
            story.append(Paragraph(f'<font color="#38a169">{line}</font>', body_style))
        else:
            story.append(Paragraph(line, body_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This report was generated automatically by ForensiGuard. "
        "Results should be reviewed by a qualified forensic examiner before use in legal proceedings.",
        ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=7, textColor=colors.grey)
    ))

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    doc.build(story)

    return pdf_path