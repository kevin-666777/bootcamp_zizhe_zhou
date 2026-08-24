# AAPL Next-Day Volatility Forecasting

## Project Summary

Portfolio risk teams must decide how much market exposure they are willing to carry before the next trading session, but risk can change faster than a static historical average suggests. This project will build a reproducible workflow that uses information available by the end of each trading day—such as AAPL returns, price range, and trading volume—to estimate the magnitude of AAPL's next-day price movement. The initial target will be next-day absolute close-to-close return, a simple and transparent proxy for realized volatility.

The project is intended to support risk monitoring, not to recommend trades or predict price direction. Its output will help a portfolio risk analyst identify unusually high expected-volatility days, compare the forecast with a rolling historical-volatility baseline, and decide whether additional review, tighter risk limits, or hedging discussion is warranted. The project matters because an explainable and consistently evaluated warning signal can make daily risk reviews more focused while keeping uncertainty and model limitations visible.

## Stakeholder Persona & Context

**Primary stakeholder:** Portfolio risk analyst responsible for monitoring a portfolio with material AAPL exposure.

The analyst reviews market and portfolio risk near the end of each trading day and prepares guidance for the next session. They care about timely, stable, and explainable risk estimates more than a complex model with small in-sample gains. They need to understand what information drove the signal, how it compares with a simple baseline, and whether the model is operating in a market regime represented by its training history.

**Decision supported:** Determine whether the next trading day requires routine monitoring or an elevated-risk review. An elevated signal may prompt the analyst to inspect concentration, discuss hedging or exposure limits with the portfolio manager, or monitor the position more closely. The forecast is one input to that workflow; it does not automatically execute a trade.

**Timing:** The feature set and forecast must be available after the current market close and before the next market open. Every feature must therefore use only information known by the forecast cutoff.

## Useful Answer & Success Criteria

This is a **predictive** problem. The primary artifact will be a next-day volatility estimate accompanied by a baseline comparison, recent model diagnostics, and a plain-language risk summary.

Initial evaluation will use time-ordered or walk-forward validation. The primary metric will be mean absolute error (MAE), with RMSE and tail-period diagnostics reported as secondary checks. A rolling historical-volatility estimate will serve as the baseline. A provisional success criterion is at least a 5% reduction in held-out MAE versus the baseline without materially worse performance during high-volatility periods. This threshold will be reviewed after data coverage and baseline variability are better understood.

## Scope

### In scope

- Daily AAPL OHLCV data and leakage-safe features derived from it
- Next-day absolute return as the first volatility target
- Transparent baselines and relatively simple predictive models
- Time-aware validation, error analysis, and regime/tail diagnostics
- Reproducible ingestion, preprocessing, feature engineering, and reporting
- A stakeholder-facing summary of forecast uncertainty and limitations

### Out of scope for the first version

- Intraday or real-time forecasting
- Automated order execution or direct buy/sell recommendations
- Portfolio optimization across multiple securities
- Options-implied volatility, news, social-media, or macroeconomic features
- Production deployment with guaranteed uptime or latency
- Claims of causal impact

## Assumptions & Constraints

- Historical daily OHLCV data are sufficiently accurate and adjusted consistently for corporate actions.
- End-of-day data are available before the analyst's forecast deadline.
- Recent historical relationships contain some information about near-term volatility, although they may change across market regimes.
- The initial dataset may be small; model complexity must remain proportional to the number of time-ordered observations.
- Features, transformations, and scalers must be fitted using training data only to prevent leakage.
- Missing trading dates must be interpreted using an exchange calendar rather than filled as ordinary weekdays.
- Compute, storage, and project time are limited to normal student resources.
- The output is an educational prototype and not investment advice.

## Known Unknowns & Risks

- **Regime change:** Relationships learned in calm periods may fail during shocks. Use walk-forward evaluation and report performance by volatility regime.
- **Tail underestimation:** Average-error metrics can hide poor performance on the days that matter most. Add tail-period and threshold-based diagnostics.
- **Limited data:** A short history can create unstable correlations and misleading apparent seasonality. Expand the date range before final modeling.
- **Target definition:** Absolute return is transparent but is only one realized-volatility proxy. Compare it with squared return or range-based targets later if justified.
- **Data leakage:** Rolling features, scaling, and target alignment can accidentally use future rows. Add alignment tests and time-aware pipelines.
- **Corporate actions and data revisions:** Splits, dividends, or vendor changes may create artificial jumps. Validate adjusted-price behavior and preserve raw snapshots.
- **Actionability:** Even an accurate forecast may not justify a hedge after costs and portfolio context. Keep the model advisory and document the human decision step.

## Goals → Lifecycle → Deliverables

| Goal | Lifecycle stage | Deliverable |
|---|---|---|
| Define the risk decision, stakeholder, forecast cutoff, and scope | Problem Framing & Scoping | Project README and stakeholder memo |
| Create a reproducible Python environment and secure configuration | Tooling Setup | Environment specification, `.env.example`, dependency file, and project scaffold |
| Acquire trustworthy historical AAPL data | Data Acquisition & Ingestion | Versioned raw OHLCV snapshots, source documentation, and ingestion validation |
| Preserve raw data and efficient analytical copies | Data Storage | Environment-driven CSV/Parquet storage utilities and documented folder conventions |
| Clean schema, dates, missing values, and corporate-action anomalies | Data Preprocessing | Reusable cleaning functions and validated processed dataset |
| Identify skew, outliers, regime changes, and temporal structure | EDA & Risk Review | Executed EDA notebook, plots, assumptions, and risk notes |
| Build leakage-safe lag, rolling-volatility, range, volume, and calendar features | Feature Engineering | Reusable feature module and model-ready feature table |
| Establish a transparent benchmark | Baseline Modeling | Rolling-volatility baseline with walk-forward MAE/RMSE |
| Test whether a simple model improves on the baseline | Modeling & Evaluation | Time-aware pipeline, comparison table, residual/tail diagnostics, and model artifact |
| Explain the signal and its limitations to the risk analyst | Communication & Delivery | Final report/dashboard, model card, and stakeholder recommendation |
| Monitor data and performance drift | Monitoring | Data-quality checks, rolling error metrics, and retraining/review triggers |

## Repository Plan

```text
project/
├── data/
│   ├── raw/          # Immutable source snapshots
│   └── processed/    # Clean and feature-ready data
├── docs/             # Stakeholder briefs, model card, and decisions
├── model/            # Serialized model and metadata
├── notebooks/        # Numbered analysis notebooks
├── reports/          # Figures, tables, and final outputs
├── src/              # Reusable ingestion, cleaning, features, and modeling code
├── .env.example      # Safe configuration template
├── .gitignore
├── Makefile           # Shortcuts for setup, checks, and Jupyter
├── requirements.txt  # Reproducible Python dependencies
└── README.md
```

Changes will be made in small, descriptive commits. Raw data will be preserved, derived data will be reproducible from code, and material changes to target, scope, assumptions, or evaluation will be recorded in this README or `docs/`.

## Tooling Setup

The project targets **Python 3.11** and uses a dedicated Conda environment. From the repository root, recreate the environment and install the dependencies with:

```bash
conda create -n fe-course python=3.11 -y
conda activate fe-course
cd project
python -m pip install -r requirements.txt
```

Create the local configuration file from the safe template. The resulting `.env` is excluded by `.gitignore` and must never contain committed credentials.

```bash
cp .env.example .env
```

Configuration is loaded through `src/config.py`. `load_env()` reads the project-level `.env`, `get_key()` retrieves a setting with optional required-value validation, and `get_path()` resolves data and artifact directories relative to the project root. A typical notebook setup is:

```python
from src.config import get_path, load_env

load_env()
raw_dir = get_path("DATA_DIR_RAW", "data/raw", create=True)
```

The `Makefile` provides three convenience commands:

- `make install` installs the pinned dependencies.
- `make check` checks that the source modules compile.
- `make notebook` starts JupyterLab in the active environment.

The scaffold separates immutable source snapshots in `data/raw/`, reproducible derived datasets in `data/processed/`, exploratory work in `notebooks/`, reusable logic in `src/`, stakeholder documentation in `docs/`, generated outputs in `reports/`, and model artifacts in `model/`. Empty folders contain `.gitkeep` so the full structure remains visible on GitHub.

## Current Stage

**Tooling Setup complete.** The project now has a reproducible dependency specification, environment-driven configuration, a secure secrets template, executable setup shortcuts, and the full lifecycle scaffold. The next stage will acquire and validate historical AAPL market data.
