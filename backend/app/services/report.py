"""Generate PDF evidence dossier for an investigation."""
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

NAVY = colors.HexColor("#0F1E33")
ACCENT = colors.HexColor("#1F90DF")
TEXT = colors.HexColor("#1A3A5C")
MUTED = colors.HexColor("#5A7191")
LIGHT = colors.HexColor("#EBE0DC")


def _styles():
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=ss["Heading1"],
            textColor=ACCENT, fontSize=22, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=ss["Normal"],
            textColor=MUTED, fontSize=10, spaceAfter=16,
        ),
        "h2": ParagraphStyle(
            "h2", parent=ss["Heading2"],
            textColor=NAVY, fontSize=14, spaceBefore=12, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", parent=ss["Normal"],
            textColor=TEXT, fontSize=10, leading=14,
        ),
        "small": ParagraphStyle(
            "small", parent=ss["Normal"],
            textColor=MUTED, fontSize=8, leading=11,
        ),
        "mono": ParagraphStyle(
            "mono", parent=ss["Normal"],
            fontName="Courier", fontSize=9, textColor=TEXT,
        ),
    }


def _cell_para(text, bold=False, align="left"):
    alignment_map = {"left": 0, "center": 1, "right": 2}
    alignment_val = alignment_map.get(align, 0)

    style = ParagraphStyle(
        f"cell_{align}",
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.white if bold else TEXT,
        alignment=alignment_val,  # type: ignore[arg-type]
    )
    return Paragraph(str(text), style)


def generate_report(investigation: dict) -> bytes:
    """Generate a PDF evidence dossier from an investigation dict."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"MARITRACE Dossier {investigation.get('case_number', '')}",
    )
    st = _styles()
    story = []

    # ── Header ──────────────────────────────────────────────────
    story.append(Paragraph("MARITRACE", st["title"]))
    story.append(Paragraph(
        "Marine Oil Spill Intelligence · Evidence Dossier", st["subtitle"],
    ))

    case_no = investigation.get("case_number", "—")
    slick_id = investigation.get("slick_id", "—")
    origin = investigation.get("origin", {}) or {}
    region_label = investigation.get("region_label", "Unknown Region")
    source = investigation.get("source", "live")

    info_data = [
        [_cell_para("Filing Region", True), _cell_para(str(region_label))],
        [_cell_para("Detection Source", True),
         _cell_para("Historical Archive" if source == "historical" else "Live (last 72h)")],
        [_cell_para("Case Number", True), _cell_para(str(case_no))],
        [_cell_para("Slick ID", True), _cell_para(str(slick_id))],
        [_cell_para("Origin Latitude", True), _cell_para(f"{origin.get('lat', 0):.5f}")],
        [_cell_para("Origin Longitude", True), _cell_para(f"{origin.get('lon', 0):.5f}")],
        [_cell_para("Hindcast Origin Time (UTC)", True),
         _cell_para(str(origin.get("time", "—")))],
        [_cell_para("Report Generated (UTC)", True),
         _cell_para(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))],
        [_cell_para("Team", True), _cell_para("AstraX-22 · SIH 2026 · PS 26143")],
    ]
    info_tbl = Table(info_data, colWidths=[6*cm, 11*cm])
    info_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, MUTED),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, MUTED),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 0.6*cm))

    # ── Method ──────────────────────────────────────────────────
    story.append(Paragraph("Methodology Summary", st["h2"]))
    method_text = (
        "Oil-spill detections are sourced from Cerulean (SkyTruth) using Sentinel-1 SAR imagery. "
        "For each detection, a Lagrangian hindcast is run backward in time over 72 hours using "
        "ocean-current fields (Open-Meteo Marine) and 10-metre wind fields (Open-Meteo Forecast), "
        "with a 3% wind-drift factor and Ekman rotation. The endpoint cloud is bounded by a convex "
        "hull to produce a probable-origin cone. Candidate vessels are then retrieved from the live "
        "AIS feed within a 50 km radius of the origin and ranked via a 5-factor weighted model."
    )
    story.append(Paragraph(method_text, st["body"]))
    story.append(Spacer(1, 0.4*cm))

    # ── Ranking model ───────────────────────────────────────────
    story.append(Paragraph("Ranking Model Weights", st["h2"]))
    weights_data = [
        [_cell_para("Factor", True), _cell_para("Weight", True, "center"),
         _cell_para("Rationale", True)],
        [_cell_para("Spatial proximity"), _cell_para("30%", False, "center"),
         _cell_para("Distance from vessel to hindcast origin")],
        [_cell_para("Temporal correlation"), _cell_para("25%", False, "center"),
         _cell_para("Time overlap with probable release window")],
        [_cell_para("Trajectory alignment"), _cell_para("25%", False, "center"),
         _cell_para("Course similarity with slick drift direction")],
        [_cell_para("Drift consistency"), _cell_para("10%", False, "center"),
         _cell_para("Fraction of track inside hindcast cone")],
        [_cell_para("Behaviour anomaly"), _cell_para("10%", False, "center"),
         _cell_para("AIS gaps, sudden slowdowns, erratic turns")],
    ]
    weights_tbl = Table(weights_data, colWidths=[5*cm, 2*cm, 10*cm])
    weights_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("BOX", (0, 0), (-1, -1), 0.5, MUTED),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, MUTED),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(weights_tbl)
    story.append(Spacer(1, 0.6*cm))

    # ── Candidates ──────────────────────────────────────────────
    candidates = investigation.get("candidates", [])
    story.append(Paragraph(
        f"Ranked Candidate Vessels ({len(candidates)})", st["h2"],
    ))

    if not candidates:
        story.append(Paragraph(
            "No candidate vessels were identified within the search radius.",
            st["body"],
        ))
    else:
        header = [
            _cell_para("Rank", True, "center"),
            _cell_para("MMSI", True, "center"),
            _cell_para("Dist (km)", True, "center"),
            _cell_para("Spatial", True, "center"),
            _cell_para("Temporal", True, "center"),
            _cell_para("Trajectory", True, "center"),
            _cell_para("Drift", True, "center"),
            _cell_para("Anomaly", True, "center"),
            _cell_para("Total", True, "center"),
        ]
        rows = [header]
        for c in candidates[:20]:
            rows.append([
                _cell_para(c.get("rank", "—"), True, "center"),
                _cell_para(c.get("mmsi", "—"), False, "center"),
                _cell_para(f"{c.get('min_distance_km', 0):.2f}", False, "center"),
                _cell_para(f"{c.get('spatial_score', 0):.1f}", False, "center"),
                _cell_para(f"{c.get('temporal_score', 0):.1f}", False, "center"),
                _cell_para(f"{c.get('trajectory_score', 0):.1f}", False, "center"),
                _cell_para(f"{c.get('drift_score', 0):.1f}", False, "center"),
                _cell_para(f"{c.get('anomaly_score', 0):.1f}", False, "center"),
                _cell_para(f"{c.get('total_score', 0):.1f}%", True, "center"),
            ])
        cand_tbl = Table(
            rows,
            colWidths=[1.2*cm, 2.4*cm, 1.8*cm, 1.6*cm, 1.8*cm, 2*cm, 1.4*cm, 1.8*cm, 1.8*cm],
            repeatRows=1,
        )
        cand_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("BOX", (0, 0), (-1, -1), 0.5, MUTED),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, MUTED),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F1EE")]),
        ]))
        story.append(cand_tbl)
        story.append(Spacer(1, 0.4*cm))

        top = candidates[0]
        summary = (
            f"<b>Primary candidate:</b> MMSI {top.get('mmsi')} "
            f"with an association score of {top.get('total_score', 0):.1f}% "
            f"({top.get('min_distance_km', 0):.2f} km from origin). "
            "This vessel should be treated as a high-priority subject for further investigation."
        )
        story.append(Paragraph(summary, st["body"]))

    story.append(Spacer(1, 0.6*cm))

    # ── Disclaimer ──────────────────────────────────────────────
    story.append(Paragraph("Disclaimer", st["h2"]))
    story.append(Paragraph(
        "This document is an automated evidence summary generated by MARITRACE from public "
        "data sources (Cerulean / SkyTruth, AISStream, Open-Meteo). Scores are probabilistic "
        "and do not establish legal liability. All findings should be independently verified "
        "against original satellite imagery and authoritative AIS archives before action.",
        st["small"],
    ))

    doc.build(story)
    return buf.getvalue()