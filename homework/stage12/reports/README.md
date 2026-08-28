# Stage 12 Reporting Deliverables

## Audience and rationale

The primary audience is a portfolio risk analyst monitoring material AAPL exposure. The analyst needs a fast answer to three questions: whether the model is useful, when it becomes unreliable, and what action its signal should trigger.

## Why this format fits

The PDF is a short, fixed-layout decision brief that can be reviewed before the next market session, shared without a notebook environment, and archived with model-governance materials. It emphasizes headlines, consistent charts, quantified sensitivity, assumptions, and an operating recommendation. The executed notebook is the companion technical format: it reproduces every metric, chart, bootstrap interval, and exported report input for peer review.

## Files

- `final_report.pdf` - primary stakeholder deliverable.
- `final_report.md` - accessible narrative version and report source.
- `images/forecast_vs_actual.png` - held-out forecast behavior.
- `images/model_scenario_sensitivity.png` - Ridge versus Huber scenario comparison.
- `images/regime_risk_comparison.png` - calm versus elevated-regime MAE.
- `sensitivity_summary.csv` - quantified scenario changes and implications.
- `summary_metrics.json` - machine-readable inputs used to build the PDF.

Regenerate the analysis by running `homework12_results-reporting-delivery-design_submission.ipynb` from the repository. Then run `src/reporting.py` through the bundled ReportLab environment or call `build_stakeholder_pdf()` with the generated summary, image directory, and target PDF path.
