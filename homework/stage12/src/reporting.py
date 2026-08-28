"""Build the Stage 12 stakeholder PDF from executed analysis artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


NAVY = colors.HexColor("#17324D")
TEAL = colors.HexColor("#1F7A8C")
ORANGE = colors.HexColor("#F28E2B")
RED = colors.HexColor("#C44536")
LIGHT = colors.HexColor("#EEF3F6")
MID = colors.HexColor("#637381")


def build_stakeholder_pdf(
    summary_path: str | Path,
    image_dir: str | Path,
    output_path: str | Path,
) -> Path:
    """Create a polished four-page decision report for a risk analyst."""
    summary = json.loads(Path(summary_path).read_text())
    images = Path(image_dir)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    styles = _styles()
    document = SimpleDocTemplate(
        str(destination),
        pagesize=letter,
        leftMargin=0.62 * inch,
        rightMargin=0.62 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
        title="AAPL Next-Day Volatility Forecast - Stakeholder Report",
        author="Kevin Zhou",
        subject="Stage 12 Results, Reporting, and Delivery Design",
    )
    story = []

    story.extend(_title_page(summary, styles))
    story.append(PageBreak())
    story.extend(_forecast_page(summary, images, styles))
    story.append(PageBreak())
    story.extend(_sensitivity_page(summary, images, styles))
    story.append(PageBreak())
    story.extend(_decision_page(summary, styles))

    document.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return destination


def _title_page(summary: dict, styles: dict) -> list:
    ridge = summary["models"]["Ridge"]
    block = summary["uncertainty"]["block_bootstrap_95"]
    return [
        Spacer(1, 0.15 * inch),
        Paragraph("AAPL Next-Day Volatility Forecast", styles["title"]),
        Paragraph("Decision brief for portfolio risk monitoring", styles["subtitle"]),
        Spacer(1, 0.25 * inch),
        _label("EXECUTIVE SUMMARY", styles),
        Paragraph(
            "<b>Use as a monitoring baseline, not an automated risk control.</b> "
            "The model adds useful next-day ranking information but can miss the size of genuine shocks.",
            styles["lead"],
        ),
        _bullet("Average held-out miss is 0.93 percentage points of daily absolute return.", styles),
        _bullet("Error rises about 31% when current 21-day volatility is elevated.", styles),
        _bullet("Robust Huber loss improves typical-day MAE, but slightly worsens RMSE and does not solve tail misses.", styles),
        Spacer(1, 0.22 * inch),
        _recommendation_box(styles),
        Spacer(1, 0.28 * inch),
        _label("DECISION METRICS", styles),
        _kpi_table(
            [
                ("RIDGE TEST MAE", f"{ridge['MAE'] * 100:.2f} pp", "Typical absolute miss"),
                ("RIDGE TEST R2", f"{ridge['R2']:.2f}", "Out-of-sample variance explained"),
                ("BLOCK 95% CI", f"{block[0] * 100:.2f}-{block[1] * 100:.2f} pp", "Average-MAE uncertainty"),
                ("ELEVATED MAE", f"{summary['subgroups']['Ridge']['elevated']['MAE'] * 100:.2f} pp", "Harder operating regime"),
            ],
            styles,
        ),
        Spacer(1, 0.28 * inch),
        Paragraph(
            f"Evaluation window: {summary['test_period']['start']} to {summary['test_period']['end']} | "
            f"{summary['test_period']['rows']} daily forecasts | Target: next-session absolute adjusted-close return",
            styles["footnote"],
        ),
    ]


def _forecast_page(summary: dict, images: Path, styles: dict) -> list:
    maximum = summary["tail_check"]
    return [
        _label("1 | FORECAST BEHAVIOR", styles),
        Paragraph("The model tracks changing risk levels, but compresses the largest shocks", styles["h1"]),
        Paragraph(
            "The orange forecast responds to recent volatility and usually stays near the center of realized outcomes. "
            "That stability helps routine monitoring, but it also smooths the events a risk team cares about most.",
            styles["body"],
        ),
        Spacer(1, 0.1 * inch),
        Image(str(images / "forecast_vs_actual.png"), width=6.65 * inch, height=3.46 * inch),
        Spacer(1, 0.12 * inch),
        _takeaway_box(
            "WHAT THE CHART SHOWS",
            f"On forecast date {maximum['forecast_date']}, the next-day move was {maximum['actual'] * 100:.2f}% "
            f"while Ridge forecast {maximum['predicted'] * 100:.2f}%. The model identified higher risk but "
            "understated its magnitude.",
            styles,
        ),
        Spacer(1, 0.12 * inch),
        Paragraph(
            "Assumption / limitation: historical lag, range, volume, and rolling-volatility relationships are assumed "
            "to carry forward. A regime break or event outside the training experience can invalidate that assumption.",
            styles["footnote"],
        ),
    ]


def _sensitivity_page(summary: dict, images: Path, styles: dict) -> list:
    return [
        _label("2 | SENSITIVITY AND HIDDEN FAILURE", styles),
        Paragraph("The preferred model depends on the cost of typical misses versus tail misses", styles["h1"]),
        Paragraph(
            "Two alternate assumptions are tested on the same held-out dates: squared-loss Ridge and robust-loss Huber. "
            "The regime split uses only current 21-day volatility and a threshold estimated from training data.",
            styles["body"],
        ),
        Spacer(1, 0.08 * inch),
        Image(str(images / "model_scenario_sensitivity.png"), width=7.1 * inch, height=2.55 * inch),
        Spacer(1, 0.08 * inch),
        Paragraph(
            "Huber lowers MAE by 5.4%, but raises RMSE by 1.2%. It improves the typical day while giving up a small "
            "amount of large-error performance. This is a stakeholder loss-function decision, not a universal win.",
            styles["caption"],
        ),
        Spacer(1, 0.12 * inch),
        Image(str(images / "regime_risk_comparison.png"), width=7.1 * inch, height=2.55 * inch),
        Spacer(1, 0.08 * inch),
        Paragraph(
            f"Ridge MAE increases from {summary['subgroups']['Ridge']['calm']['MAE'] * 100:.2f} pp in calm conditions "
            f"to {summary['subgroups']['Ridge']['elevated']['MAE'] * 100:.2f} pp when 21-day volatility exceeds "
            f"{summary['regime_threshold'] * 100:.2f}%. Overall MAE hides this operating-regime gap.",
            styles["caption"],
        ),
    ]


def _decision_page(summary: dict, styles: dict) -> list:
    gaussian = summary["uncertainty"]["gaussian_95"]
    iid = summary["uncertainty"]["iid_bootstrap_95"]
    block = summary["uncertainty"]["block_bootstrap_95"]
    sensitivity_rows = [
        ["Assumption / scenario", "Change from baseline", "Decision meaning"],
        ["Huber robust loss", "MAE -5.4%; RMSE +1.2%", "Better typical day; no tail-risk cure"],
        ["Elevated volatility", "Ridge MAE +30.5%", "Require human review / wider buffer"],
        ["5-day dependence", "CI width +21% vs IID", "Use block interval for planning"],
    ]
    return [
        _label("3 | ASSUMPTIONS, RISKS, AND ACTION", styles),
        Paragraph("What this means for the risk analyst", styles["h1"]),
        _takeaway_box(
            "RECOMMENDED OPERATING RULE",
            f"Use the score to rank next-day attention. When current 21-day daily volatility is above "
            f"{summary['regime_threshold'] * 100:.2f}%, elevate the review and do not rely on the point forecast alone.",
            styles,
        ),
        Spacer(1, 0.18 * inch),
        _label("UNCERTAINTY IN AVERAGE TEST MAE", styles),
        Table(
            [
                ["Method", "95% interval (percentage points)", "What it assumes"],
                ["Gaussian", f"{gaussian[0]*100:.2f} - {gaussian[1]*100:.2f}", "Independent errors; normal mean approximation"],
                ["IID bootstrap", f"{iid[0]*100:.2f} - {iid[1]*100:.2f}", "Observed dates are exchangeable"],
                ["5-day block", f"{block[0]*100:.2f} - {block[1]*100:.2f}", "Short local dependence is retained"],
            ],
            colWidths=[1.25 * inch, 2.1 * inch, 3.55 * inch],
            style=_table_style(),
        ),
        Spacer(1, 0.2 * inch),
        _label("SENSITIVITY SUMMARY", styles),
        Table(
            sensitivity_rows,
            colWidths=[1.55 * inch, 1.65 * inch, 3.7 * inch],
            style=_table_style(),
        ),
        Spacer(1, 0.2 * inch),
        _label("KEY ASSUMPTIONS AND RISKS", styles),
        _bullet("Data and feature relationships remain similar to the 2020-2026 history.", styles),
        _bullet("The close-to-next-close target is a risk proxy, not a portfolio loss forecast or causal estimate.", styles),
        _bullet("Average-error intervals do not cover refitting uncertainty, data revisions, or an unseen crisis regime.", styles),
        _bullet("Correlated rolling features and changing volatility regimes can destabilize coefficients and calibration.", styles),
        Spacer(1, 0.14 * inch),
        _label("NEXT CONTROL STEPS", styles),
        Paragraph(
            "1. Run rolling-origin refits and publish tail MAE and high-volatility recall. &nbsp;&nbsp; "
            "2. Add block-bootstrap or conformal prediction intervals. &nbsp;&nbsp; "
            "3. Require human review above the volatility threshold. &nbsp;&nbsp; "
            "4. Do not automate hedges or exposure limits from this prototype.",
            styles["body"],
        ),
    ]


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=25, leading=29, textColor=NAVY, alignment=TA_LEFT, spaceAfter=7),
        "subtitle": ParagraphStyle("Subtitle", parent=base["Normal"], fontName="Helvetica", fontSize=12.5, leading=16, textColor=TEAL, spaceAfter=8),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=NAVY, spaceAfter=9),
        "lead": ParagraphStyle("Lead", parent=base["BodyText"], fontName="Helvetica", fontSize=11.5, leading=16, textColor=NAVY, spaceAfter=10),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=colors.HexColor("#263746"), spaceAfter=6),
        "bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName="Helvetica", fontSize=10, leading=14, leftIndent=15, firstLineIndent=-10, textColor=colors.HexColor("#263746"), spaceAfter=5),
        "label": ParagraphStyle("Label", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=TEAL, tracking=1.2, spaceAfter=8),
        "box_head": ParagraphStyle("BoxHead", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=TEAL, spaceAfter=4),
        "box_body": ParagraphStyle("BoxBody", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=NAVY),
        "caption": ParagraphStyle("Caption", parent=base["BodyText"], fontName="Helvetica", fontSize=8.8, leading=12.2, textColor=colors.HexColor("#354A5F"), spaceAfter=5),
        "footnote": ParagraphStyle("Footnote", parent=base["BodyText"], fontName="Helvetica-Oblique", fontSize=8, leading=11, textColor=MID),
        "kpi_value": ParagraphStyle("KPIValue", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=14, leading=17, textColor=NAVY, alignment=TA_CENTER),
        "kpi_label": ParagraphStyle("KPILabel", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=TEAL, alignment=TA_CENTER),
        "kpi_note": ParagraphStyle("KPINote", parent=base["Normal"], fontName="Helvetica", fontSize=7, leading=9, textColor=MID, alignment=TA_CENTER),
    }


def _label(text: str, styles: dict) -> Paragraph:
    return Paragraph(text, styles["label"])


def _bullet(text: str, styles: dict) -> Paragraph:
    return Paragraph(f"- {text}", styles["bullet"])


def _recommendation_box(styles: dict) -> Table:
    content = [
        Paragraph("RECOMMENDATION", styles["box_head"]),
        Paragraph(
            "Adopt for daily triage with a human escalation rule. Do not use the point estimate to automate hedges, "
            "position limits, or trade execution.",
            styles["box_body"],
        ),
    ]
    return Table([[content]], colWidths=[7.05 * inch], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 1.2, TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))


def _takeaway_box(title: str, body: str, styles: dict) -> Table:
    return Table(
        [[[Paragraph(title, styles["box_head"]), Paragraph(body, styles["box_body"])]]],
        colWidths=[7.05 * inch],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
            ("LINEBEFORE", (0, 0), (0, -1), 4, ORANGE),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]),
    )


def _kpi_table(items: list[tuple[str, str, str]], styles: dict) -> Table:
    cells = []
    for label, value, note in items:
        cells.append([Paragraph(label, styles["kpi_label"]), Paragraph(value, styles["kpi_value"]), Paragraph(note, styles["kpi_note"])])
    table = Table([cells], colWidths=[1.76 * inch] * 4)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5DC")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8E0E5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return table


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D1D8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])


def _page_footer(canvas, document) -> None:
    canvas.saveState()
    width, _ = letter
    canvas.setStrokeColor(colors.HexColor("#D5DEE4"))
    canvas.line(0.62 * inch, 0.44 * inch, width - 0.62 * inch, 0.44 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MID)
    canvas.drawString(0.62 * inch, 0.27 * inch, "AAPL volatility forecast | Educational prototype - not investment advice")
    canvas.drawRightString(width - 0.62 * inch, 0.27 * inch, f"Page {document.page}")
    canvas.restoreState()
