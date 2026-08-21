# Stock Volatility Forecasting

**Stage:** Problem Framing & Scoping (Stage 01)

## Problem Statement

Stock prices can move sharply from one trading day to the next, making market risk difficult to summarize using only recent returns. This student project will explore whether historical price and volume data can be used to predict the next trading day's volatility for a selected stock or market index. A useful result would help explain when volatility is likely to rise or fall and provide a simple, reproducible example of a predictive data science workflow.

The project is an educational prototype, not a production trading system. Success will be measured by comparing a basic volatility forecast with a simple baseline, such as the recent rolling-average volatility. The main goal is to demonstrate clear problem framing, appropriate evaluation, and honest communication of uncertainty rather than to generate investment advice.

## Stakeholder & User

The primary stakeholder and reader is the course instructor, who will evaluate whether the project connects a well-defined problem to a suitable data science lifecycle and deliverable. The student is the primary user and will use the output to practice data collection, feature engineering, modeling, evaluation, and stakeholder communication. The prototype may be reviewed during class or at assignment checkpoints; it is not intended for real-time financial decisions.

## Useful Answer & Decision

This is a **predictive** question: estimate next-day realized volatility from information available at the end of the current trading day. The main artifact will be a notebook or report containing the forecast, a comparison with a rolling-volatility baseline, and a plain-language summary. Example evaluation metrics are mean absolute error (MAE) and root mean squared error (RMSE). The decision supported is academic: whether the proposed features and model improve meaningfully over the baseline and are worth developing in later project stages.

## Assumptions & Constraints

- Historical daily price and volume data are available and sufficiently accurate.
- Adjusted closing prices account for stock splits and dividends when appropriate.
- All predictors use only information available before the forecast date to avoid data leakage.
- Daily data are adequate for this classroom prototype; intraday volatility is out of scope.
- Compute time, storage, and project duration are limited to normal student resources.
- The output is educational and must not be treated as financial or investment advice.

## Known Unknowns / Risks

- The target stock or index and final date range have not yet been selected.
- Market regimes can change, so historical relationships may not remain stable.
- News and macroeconomic events may drive volatility but may not appear in price data alone.
- Volatility has several valid definitions; the final target definition may affect results.
- Strong performance on one security may not generalize to other securities.
- Model accuracy will be tested with time-ordered validation and monitored against a simple baseline.

## Lifecycle Mapping

- Define a stakeholder-centered volatility question → Problem Framing & Scoping (Stage 01) → Scoping paragraph and stakeholder memo
- Obtain trustworthy market data → Data Acquisition & Ingestion → Versioned raw price and volume dataset
- Create leakage-safe predictors and a volatility target → Data Preparation → Analysis-ready feature table
- Compare a predictive model with a rolling baseline → Modeling & Evaluation → Validated forecast metrics and diagnostic plots
- Explain results and limitations to the instructor → Communication & Delivery → Final notebook/report with a plain-language summary

## Repo Plan

- `data/`: raw and processed market data (large or sensitive files will not be committed)
- `src/`: reusable data preparation and modeling code
- `notebooks/`: exploration, modeling, and evaluation notebooks
- `docs/`: stakeholder-facing artifacts and project notes
- `README.md`: current scope, assumptions, lifecycle mapping, and project status

The repository will be updated at each course stage with small, descriptive commits. Scope changes, assumptions, and evaluation results will be recorded as the project develops.
