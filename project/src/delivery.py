"""Build the stakeholder-ready Stage 12 PDF from evaluated project artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#3E6F9E")
PALE_BLUE = colors.HexColor("#EAF1F7")
ORANGE = colors.HexColor("#D97732")
PALE_ORANGE = colors.HexColor("#FCEDE2")
RED = colors.HexColor("#A33A2B")
GREEN = colors.HexColor("#287A5B")
GRAY = colors.HexColor("#536270")
LIGHT_GRAY = colors.HexColor("#F4F6F8")


def _styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle", parent=sample["Title"], fontName="Helvetica-Bold",
            fontSize=28, leading=32, textColor=NAVY, alignment=TA_LEFT, spaceAfter=16,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=sample["Normal"], fontName="Helvetica",
            fontSize=13, leading=18, textColor=GRAY, spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "H1", parent=sample["Heading1"], fontName="Helvetica-Bold",
            fontSize=20, leading=24, textColor=NAVY, spaceBefore=4, spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "H2", parent=sample["Heading2"], fontName="Helvetica-Bold",
            fontSize=13, leading=16, textColor=BLUE, spaceBefore=8, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body", parent=sample["BodyText"], fontName="Helvetica",
            fontSize=9.4, leading=13.2, textColor=colors.HexColor("#24313C"), spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "Small", parent=sample["BodyText"], fontName="Helvetica",
            fontSize=7.8, leading=10.5, textColor=GRAY, spaceAfter=4,
        ),
        "callout": ParagraphStyle(
            "Callout", parent=sample["BodyText"], fontName="Helvetica-Bold",
            fontSize=12, leading=16, textColor=NAVY, alignment=TA_LEFT,
        ),
        "metric": ParagraphStyle(
            "Metric", parent=sample["BodyText"], fontName="Helvetica-Bold",
            fontSize=17, leading=20, textColor=NAVY, alignment=TA_CENTER,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel", parent=sample["BodyText"], fontName="Helvetica",
            fontSize=7.8, leading=10, textColor=GRAY, alignment=TA_CENTER,
        ),
        "table": ParagraphStyle(
            "TableText", parent=sample["BodyText"], fontName="Helvetica",
            fontSize=7.8, leading=10, textColor=colors.HexColor("#24313C"),
        ),
        "table_head": ParagraphStyle(
            "TableHead", parent=sample["BodyText"], fontName="Helvetica-Bold",
            fontSize=7.8, leading=10, textColor=colors.white,
        ),
    }


def _header_footer(canvas, doc) -> None:
    canvas.saveState()
    width, height = letter
    if doc.page > 1:
        canvas.setFillColor(NAVY)
        canvas.rect(0, height - 0.34 * inch, width, 0.34 * inch, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(0.55 * inch, height - 0.22 * inch, "AAPL NEXT-DAY VOLATILITY | RISK DECISION BRIEF")
    canvas.setStrokeColor(colors.HexColor("#CDD4DA"))
    canvas.line(0.55 * inch, 0.43 * inch, width - 0.55 * inch, 0.43 * inch)
    canvas.setFillColor(GRAY)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(0.55 * inch, 0.25 * inch, "Educational prototype - not investment advice")
    canvas.drawRightString(width - 0.55 * inch, 0.25 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def _bullets(items: list[str], style: ParagraphStyle) -> list[Paragraph]:
    return [_p(f"- {item}", style) for item in items]


def _metric_cards(styles, values: list[tuple[str, str, colors.Color]]) -> Table:
    cells = []
    for value, label, background in values:
        cells.append([
            _p(value, styles["metric"]),
            _p(label, styles["metric_label"]),
            background,
        ])
    table = Table([[Table([[cell[0]], [cell[1]]], colWidths=[2.08 * inch]) for cell in cells]], colWidths=[2.18 * inch] * len(cells))
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D4DCE3")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D4DCE3")),
    ]
    for index, cell in enumerate(cells):
        commands.append(("BACKGROUND", (index, 0), (index, 0), cell[2]))
    table.setStyle(TableStyle(commands))
    return table


def _scaled_image(path: Path, width: float, height: float) -> Image:
    image = Image(str(path))
    image._restrictSize(width, height)
    image.hAlign = "CENTER"
    return image


def build_stakeholder_report(project_root: str | Path, output_path: str | Path | None = None) -> Path:
    """Create the final stakeholder PDF from committed Stage 10-11 outputs."""
    root = Path(project_root).resolve()
    reports = root / "reports"
    output = Path(output_path).resolve() if output_path else reports / "aapl_volatility_stakeholder_report.pdf"
    required = {
        "walk_summary": reports / "aapl_walk_forward_summary.csv",
        "folds": reports / "aapl_walk_forward_folds.csv",
        "intervals": reports / "aapl_evaluation_intervals.csv",
        "scenarios": reports / "aapl_evaluation_scenarios.csv",
        "yearly": reports / "aapl_evaluation_yearly.csv",
        "walk_chart": reports / "aapl_walk_forward_diagnostics.png",
        "evaluation_chart": reports / "aapl_evaluation_uncertainty_scenarios.png",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Stakeholder report inputs are missing: {missing}")
    output.parent.mkdir(parents=True, exist_ok=True)

    walk_summary = pd.read_csv(required["walk_summary"]).set_index("method")
    folds = pd.read_csv(required["folds"])
    intervals = pd.read_csv(required["intervals"])
    scenarios = pd.read_csv(required["scenarios"]).set_index("volatility_scenario")
    yearly = pd.read_csv(required["yearly"])
    model = walk_summary.loc["selected_regression"]
    baseline = walk_summary.loc["rolling_vol_21d_baseline"]
    overall_block = intervals.query("scenario == 'All forecasts' and method == 'Moving-block bootstrap (20d)'").iloc[0]
    tail_block = intervals.query("scenario == 'High volatility' and method == 'Moving-block bootstrap (20d)'").iloc[0]
    tail = scenarios.loc["High volatility (training-defined tail)"]
    ordinary = scenarios.loc["Ordinary volatility"]

    styles = _styles()
    doc = BaseDocTemplate(
        str(output), pagesize=letter, rightMargin=0.55 * inch, leftMargin=0.55 * inch,
        topMargin=0.55 * inch, bottomMargin=0.58 * inch,
        title="AAPL Next-Day Volatility Forecasting - Stakeholder Report",
        author="AAPL Volatility Project Team",
        subject="Portfolio risk decision brief and model evaluation",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="report", frames=frame, onPage=_header_footer)])
    story = []

    story.extend([
        Spacer(1, 0.55 * inch),
        _p("AAPL Next-Day Volatility Forecasting", styles["title"]),
        _p("Stakeholder decision brief for end-of-day portfolio risk review", styles["subtitle"]),
        Spacer(1, 0.16 * inch),
        Table(
            [[_p("DECISION", styles["metric_label"]), _p("ADVISORY ONLY - NOT APPROVED FOR AUTOMATED RISK ACTION", styles["callout"])]],
            colWidths=[1.05 * inch, 5.5 * inch],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), RED), ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                ("BACKGROUND", (1, 0), (1, 0), PALE_ORANGE), ("BOX", (0, 0), (-1, -1), 0.8, RED),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]),
        ),
        Spacer(1, 0.22 * inch),
        _p("Executive takeaway", styles["h1"]),
        _p(
            "The regression improves average next-day absolute-return forecasts, but it is less accurate than the simple rolling-volatility baseline during high-volatility events. That tradeoff is unacceptable for automated hedging or limit changes. Use the model only as a secondary routine-monitoring signal, keep the baseline visible, and require human escalation for elevated risk.",
            styles["body"],
        ),
        Spacer(1, 0.12 * inch),
        _metric_cards(styles, [
            (f"{model.mae_improvement_vs_baseline_pct:.1f}%", "Average MAE improvement", PALE_BLUE),
            (f"{ordinary.mae_improvement_pct:.1f}%", "Ordinary-day improvement", PALE_BLUE),
            (f"{tail.mae_improvement_pct:.1f}%", "High-volatility improvement", PALE_ORANGE),
        ]),
        Spacer(1, 0.22 * inch),
        _p("Decision supported", styles["h2"]),
        _p("Whether AAPL exposure requires routine monitoring or an elevated-risk review before the next trading session. The forecast estimates magnitude, not price direction, and does not recommend a trade.", styles["body"]),
        _p("Evidence window", styles["h2"]),
        _p("1,047 one-time walk-forward forecasts from 2022-06-21 through 2026-08-21, using information available by the prior market close.", styles["body"]),
        Spacer(1, 0.14 * inch),
        _p("Prepared from the reproducible project pipeline | Stage 12 Delivery Design", styles["small"]),
        PageBreak(),
    ])

    story.extend([
        _p("1. Business question and approach", styles["h1"]),
        _p("Portfolio risk teams need an explainable next-session magnitude estimate that can focus attention without concealing uncertainty. The target is next-day absolute adjusted-close return, a transparent realized-volatility proxy.", styles["body"]),
        _p("Leakage-safe workflow", styles["h2"]),
        *_bullets([
            "Features use only current-close or earlier data: returns, normalized range, rolling volatility, rolling absolute return, relative volume, volume change, and calendar indicators.",
            "The first 600 model-ready observations establish the initial history; six non-overlapping expanding-window folds evaluate every later row once.",
            "Within each fold, OLS and Ridge variations are selected on historical training data; scaling and fitting are repeated without future information.",
            "The benchmark is 21-session rolling return volatility, visible on the same forecast dates.",
            "Primary metric is MAE; RMSE, R-squared, tail MAE, residual patterns, and paired uncertainty provide safeguards.",
        ], styles["body"]),
        Spacer(1, 0.08 * inch),
        _p("Headline walk-forward results", styles["h2"]),
        Table(
            [[_p("Measure", styles["table_head"]), _p("Regression", styles["table_head"]), _p("Baseline", styles["table_head"]), _p("Interpretation", styles["table_head"])],
             [_p("MAE", styles["table"]), _p(f"{model.mae:.6f}", styles["table"]), _p(f"{baseline.mae:.6f}", styles["table"]), _p(f"{model.mae_improvement_vs_baseline_pct:.2f}% lower average error", styles["table"])],
             [_p("RMSE", styles["table"]), _p(f"{model.rmse:.6f}", styles["table"]), _p(f"{baseline.rmse:.6f}", styles["table"]), _p("Regression reduces large-error influence overall", styles["table"])],
             [_p("R-squared", styles["table"]), _p(f"{model.r2:.3f}", styles["table"]), _p(f"{baseline.r2:.3f}", styles["table"]), _p("Limited explained variance; not a causal model", styles["table"])],
             [_p("Fold wins", styles["table"]), _p(f"{int((folds.model_mae < folds.baseline_mae).sum())}/{len(folds)}", styles["table"]), _p("-", styles["table"]), _p("Average MAE gain appears across all folds", styles["table"])],
            ],
            colWidths=[1.1 * inch, 1.0 * inch, 1.0 * inch, 3.35 * inch],
            repeatRows=1,
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CAD2D9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]),
        ),
        Spacer(1, 0.14 * inch),
        _p("What drives the signal", styles["h2"]),
        _p("Current intraday range is the largest positive standardized coefficient in the Stage 10a fitted model; the prior session's signed return is the largest negative coefficient. These are conditional associations, not stable causal effects. Ridge was selected in four folds and OLS in two, confirming model-form instability.", styles["body"]),
        PageBreak(),
    ])

    story.extend([
        _p("2. Performance through time", styles["h1"]),
        _p("Regression beats the baseline on fold MAE in every observed walk-forward block, while residual spikes reveal large underpredicted moves. The cumulative gap remains favorable after early variability.", styles["body"]),
        _scaled_image(required["walk_chart"], 7.0 * inch, 5.25 * inch),
        Spacer(1, 0.08 * inch),
        _p("Reading the chart", styles["h2"]),
        _p("Top left compares fold MAE on a shared axis. Top right shows cumulative out-of-sample MAE. Bottom left exposes residual clustering. Bottom right isolates training-defined tail forecasts; points far below the diagonal are dangerous underpredictions.", styles["small"]),
        PageBreak(),
    ])

    story.extend([
        _p("3. Uncertainty and scenario sensitivity", styles["h1"]),
        _p("The conclusion depends on the risk scenario, not on the interval method. Gaussian, IID-bootstrap, and 20-session moving-block intervals all favor regression overall and the baseline in the high-volatility subset.", styles["body"]),
        _scaled_image(required["evaluation_chart"], 7.0 * inch, 4.9 * inch),
        Spacer(1, 0.08 * inch),
        Table(
            [[_p("Scenario", styles["table_head"]), _p("Paired MAE difference", styles["table_head"]), _p("20d block-bootstrap 95% interval", styles["table_head"]), _p("Decision", styles["table_head"])],
             [_p("All forecasts", styles["table"]), _p(f"{overall_block.mean_mae_difference:.6f}", styles["table"]), _p(f"[{overall_block.ci_lower:.6f}, {overall_block.ci_upper:.6f}]", styles["table"]), _p("Average evidence favors regression", styles["table"])],
             [_p("High volatility", styles["table"]), _p(f"{tail_block.mean_mae_difference:.6f}", styles["table"]), _p(f"[{tail_block.ci_lower:.6f}, {tail_block.ci_upper:.6f}]", styles["table"]), _p("Tail evidence favors baseline", styles["table"])],
            ],
            colWidths=[1.25 * inch, 1.45 * inch, 2.0 * inch, 1.75 * inch],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CAD2D9")),
                ("BACKGROUND", (0, 2), (-1, 2), PALE_ORANGE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]),
        ),
        PageBreak(),
    ])

    story.extend([
        _p("4. Decision implications", styles["h1"]),
        Table(
            [[_p("Routine / ordinary volatility", styles["callout"]), _p("Elevated / shock risk", styles["callout"])],
             [_p(f"Regression MAE is {ordinary.model_mae:.6f} versus {ordinary.baseline_mae:.6f}; improvement is {ordinary.mae_improvement_pct:.2f}%.", styles["body"]),
              _p(f"Regression MAE is {tail.model_mae:.6f} versus {tail.baseline_mae:.6f}; performance is {abs(tail.mae_improvement_pct):.2f}% worse.", styles["body"])],
             [_p("Use as a secondary estimate to prioritize routine analyst attention.", styles["body"]),
              _p("Keep the baseline visible and require concentration/context review. Do not suppress an alert.", styles["body"])],
            ],
            colWidths=[3.25 * inch, 3.25 * inch],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), PALE_BLUE), ("BACKGROUND", (1, 0), (1, -1), PALE_ORANGE),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD3DA")), ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]),
        ),
        Spacer(1, 0.22 * inch),
        _p("Recommended operating rule", styles["h2"]),
        *_bullets([
            "Display regression and 21-day baseline together after each close.",
            "Treat either elevated signal as a prompt for human review of AAPL concentration, limits, and market context.",
            "Never allow regression to override a higher baseline estimate without analyst sign-off.",
            "Do not automate trading, hedging, exposure changes, or alert suppression.",
        ], styles["body"]),
        _p("Next modeling priority", styles["h2"]),
        _p("Improve tail calibration before adding interface complexity. Candidate work includes asymmetric/tail-weighted loss, quantile regression, regime-aware ensembles, options-implied volatility, and explicit alert precision/recall - all evaluated with the same time-ordered controls.", styles["body"]),
        _p("Acceptance gate", styles["h2"]),
        _p("A successor must retain a below-zero paired-error interval overall and avoid materially worse tail MAE across multiple recent windows. Any change to target, features, threshold, data source, or window design requires revalidation and approval.", styles["body"]),
        PageBreak(),
    ])

    risk_rows = [
        ("Regime change", "Historical relationships may fail abruptly.", "Rolling subgroup metrics, residual clusters, out-of-range alerts."),
        ("Tail underprediction", "Large moves are understated despite average gains.", "Tail MAE, underprediction magnitude, missed elevated events."),
        ("Data/vendor risk", "Revisions or stale data can corrupt features.", "Freshness, schema, duplicate, missingness, OHLCV checks."),
        ("Interval assumptions", "IID/normal assumptions can understate uncertainty.", "Moving-block interval and block-length sensitivity."),
        ("Model instability", "OLS/Ridge choice and coefficients vary by fold.", "Selection frequency, coefficient drift, scheduled review."),
        ("Actionability", "Forecast gains may not offset costs or concentration.", "Human review, portfolio context, logged overrides."),
    ]
    story.extend([
        _p("5. Assumptions, risks, and controls", styles["h1"]),
        _p("Core assumptions", styles["h2"]),
        *_bullets([
            "Adjusted OHLCV history is accurate, timely, and consistently revised.",
            "Features are available after the current close and before the next-session decision.",
            "Expanding history remains relevant enough to inform future regimes.",
            "Absolute return and the training-period 80th percentile are useful volatility and tail proxies.",
            "A 20-session circular block captures material short-run error dependence.",
        ], styles["body"]),
        Spacer(1, 0.08 * inch),
        Table(
            [[_p("Risk", styles["table_head"]), _p("Why it matters", styles["table_head"]), _p("Required control", styles["table_head"])]]
            + [[_p(a, styles["table"]), _p(b, styles["table"]), _p(c, styles["table"])] for a, b, c in risk_rows],
            colWidths=[1.2 * inch, 2.45 * inch, 2.85 * inch], repeatRows=1,
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CAD2D9")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]),
        ),
        Spacer(1, 0.12 * inch),
        _p("Monitoring triggers", styles["h2"]),
        _p("Pause or escalate on stale/invalid inputs, a sustained non-negative all-day paired interval, materially worse tail MAE, clustered large residuals, a forecast regime outside training coverage, or unusual alert frequency. Retraining requires time-ordered revalidation and human approval.", styles["body"]),
        PageBreak(),
    ])

    story.extend([
        _p("Appendix: methodology and reproducibility", styles["h1"]),
        _p("Target and cutoff", styles["h2"]),
        _p("Target is next-session absolute adjusted-close return. Every predictor on date t is known by that date's close; only the target uses t+1. Rolling windows require full history and are never backfilled.", styles["body"]),
        _p("Model and validation", styles["h2"]),
        _p("Thirteen standardized predictors feed OLS and Ridge candidates. Friday is the omitted weekday reference. Each expanding fold performs historical validation, selects by MAE, refits on the complete fold history, clips magnitude forecasts at zero, and scores the untouched next block.", styles["body"]),
        _p("Uncertainty", styles["h2"]),
        _p("The estimand is paired daily model absolute error minus baseline absolute error. Gaussian, IID percentile bootstrap, and 20-session circular moving-block bootstrap intervals use identical scenario masks. Bootstrap runs use 5,000 resamples and seed 2026. For sparse tails, block adjacency is among tail events rather than necessarily consecutive sessions, so tail uncertainty remains an approximate stress diagnostic.", styles["body"]),
        _p("Reproducible artifacts", styles["h2"]),
        *_bullets([
            "notebooks/project_pipeline.ipynb - executed end-to-end analysis",
            "src/features.py, src/modeling.py, src/evaluation.py, src/delivery.py - reusable logic",
            "reports/aapl_walk_forward_*.csv and reports/aapl_evaluation_*.csv - report inputs",
            "docs/model_evaluation.md and docs/stakeholder_memo.md - detailed risk documentation",
            "tests/ - target alignment, leakage, walk-forward, bootstrap, subgroup, and delivery checks",
        ], styles["body"]),
        Spacer(1, 0.16 * inch),
        Table(
            [[_p("Scope boundary", styles["callout"])],
             [_p("Daily AAPL only. No intraday deployment, direction forecast, automated trading, multi-asset optimization, causal claim, guaranteed uptime, or investment recommendation.", styles["body"])]] ,
            colWidths=[6.5 * inch],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PALE_ORANGE), ("BACKGROUND", (0, 1), (-1, 1), LIGHT_GRAY),
                ("BOX", (0, 0), (-1, -1), 0.6, ORANGE), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]),
        ),
    ])

    doc.build(story)
    return output
