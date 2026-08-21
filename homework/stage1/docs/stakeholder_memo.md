# Stakeholder Brief — Stock Volatility Forecasting

**Audience:** Course instructor

**Cadence:** Review at course checkpoints

**Decision Supported:** Decide whether the proposed forecasting approach demonstrates a sound, useful data science workflow and should continue to later stages.

## Context

Daily stock volatility is difficult to anticipate and is a useful setting for practicing predictive modeling with time-dependent data. This project will build a small educational prototype that predicts next-day realized volatility from historical price and volume information. The work is designed to demonstrate problem framing, baseline comparison, leakage-aware validation, and clear communication rather than support actual trading.

## User and Pain Point

The instructor needs a concise way to assess whether the student has translated a broad interest in stock markets into a specific, measurable, and responsible project. The student needs a manageable project scope that can be extended across later lifecycle stages without requiring expensive data or production infrastructure.

## What You Will Receive

- A reproducible notebook or short report with next-day volatility forecasts.
- A comparison against a recent rolling-volatility baseline.
- MAE and RMSE results using time-ordered validation.
- Simple plots showing predicted versus observed volatility.
- A plain-language summary of assumptions, limitations, and possible next steps.

## Decision Trigger

Continue developing the model if it performs consistently better than the rolling baseline on held-out, time-ordered data and the improvement is understandable and reproducible. If it does not, document the result and simplify or revise the target and features rather than claiming unsupported predictive value.

## Assumptions and Constraints

- Historical daily market data are available and appropriate for a classroom prototype.
- Predictors will be constructed only from information known before each forecast.
- The initial model will cover one selected stock or broad market index.
- Intraday data, live deployment, transaction costs, and trading execution are out of scope.
- Results are educational and are not financial advice.

## Risks and Mitigations

- **Regime change:** Use time-ordered evaluation and report performance over different periods.
- **Data leakage:** Lag features and verify that each row uses only past information.
- **Weak signal:** Compare with a simple baseline and report negative results honestly.
- **Limited generalization:** State clearly which security and date range were tested.
- **Ambiguous volatility definition:** Document the chosen target before modeling.
