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
├── tests/             # Automated checks for reusable project code
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
- `make test` runs the utility test suite.
- `make notebook` starts JupyterLab in the active environment.

The scaffold separates immutable source snapshots in `data/raw/`, reproducible derived datasets in `data/processed/`, exploratory work in `notebooks/`, reusable logic in `src/`, stakeholder documentation in `docs/`, generated outputs in `reports/`, and model artifacts in `model/`. Empty folders contain `.gitkeep` so the full structure remains visible on GitHub.

## Data Acquisition

The initial project dataset is daily AAPL OHLCV market data from Yahoo Finance, retrieved through `yfinance`. The local `.env` supplies `MARKET_DATA_TICKER`, `MARKET_DATA_START`, and the exclusive `MARKET_DATA_END`; `.env.example` documents these settings without storing credentials. The fixed initial request covers 2020-01-01 through 2026-08-25 (exclusive end).

`src/ingestion.py` normalizes the vendor schema, parses dates and numeric fields, validates required columns, missing values, date uniqueness and order, positive prices, non-negative volume, and daily high/low relationships. `notebooks/project_pipeline.ipynb` performs the acquisition, displays the audit report, saves the raw CSV under `data/raw/`, reloads it, and validates the round trip. Raw snapshot filenames use their actual observation range—for example, `aapl_ohlcv_20200102_20260824.csv`—so the project input remains identifiable and reproducible.

Yahoo Finance is appropriate for this educational prototype but is not a guaranteed production feed. Its availability, corrections, adjustment policy, and schema may change. The committed raw snapshot preserves the precise input used by this project; later stages will explicitly resolve adjusted versus unadjusted price usage and add exchange-calendar and distribution checks.

## Data Storage

The project uses a two-layer data layout. `data/raw/` contains immutable source snapshots in CSV format, which is portable, human-readable, and easy to audit. `data/processed/` contains Parquet copies for analysis; Parquet preserves pandas types, loads efficiently, and is more compact. A processed file at this stage is a storage-format copy, not yet a cleaned or feature-engineered dataset.

Data locations come from the uncommitted `.env`: `DATA_DIR_RAW=data/raw` and `DATA_DIR_PROCESSED=data/processed`. `src/config.py` resolves those values relative to the project root, so notebooks and scripts do not require machine-specific absolute paths. `.env.example` provides safe defaults, while `.gitignore` prevents local configuration or secrets from being committed.

`src/storage.py` provides `write_df()` and `read_df()`, which route automatically by `.csv` or `.parquet` suffix, create missing parent directories when writing, reject unsupported formats, report missing files clearly, and explain how to install a missing Parquet engine. `validate_roundtrip()` verifies matching shapes, column order, and critical dtypes after reload. The Stage 05 cells in `notebooks/project_pipeline.ipynb` read the raw CSV with the environment-driven raw directory, write the Parquet copy to the processed directory, reload both formats, and display their validation reports.

## Data Preprocessing

`src/cleaning.py` provides a reusable `clean_daily_ohlcv()` pipeline that standardizes column names, parses dates and numeric values, trims provenance text, sorts observations, retains the last record for duplicate trading dates, and removes rows whose required values are missing or violate basic OHLCV rules. It finishes by applying the ingestion validator, so an invalid cleaned table cannot silently continue downstream. `cleaning_report()` records before/after row counts, missingness, duplicates, and date coverage.

The cleaning policy is intentionally conservative. Missing market prices are dropped rather than median-filled because a fabricated price would create artificial returns and volatility. Ordinary weekends and exchange holidays are not inserted. Feature scaling is deferred until modeling, where it must be fitted on training data only to prevent leakage. Adjusted close is retained alongside unadjusted OHLC values; the future return target will use a consistently documented adjusted-price basis.

The Stage 06 cells in `notebooks/project_pipeline.ipynb` load the stored raw CSV, apply the reusable cleaner, compare the original and cleaned data, validate the result, and save `data/processed/aapl_ohlcv_clean_20200102_20260824.parquet`. The raw CSV remains the source record; all preprocessing output receives a distinct filename and can be recreated from code.

## Outlier Analysis

The primary outlier definition is the 1.5 × IQR rule applied to adjusted-close daily returns. IQR is transparent and does not require normally distributed returns. `src/outliers.py` also includes a Z-score detector, winsorization, dataframe flagging, and a reusable sensitivity summary. The pipeline compares all observations, IQR-filtered observations, and 1st/99th-percentile winsorized observations and saves a boxplot under `reports/`.

Extreme returns are retained and flagged rather than deleted because genuine shocks are essential to volatility-risk analysis. The global flag is an audit and EDA annotation—not a leakage-safe model feature—and later time-ordered modeling must estimate any threshold using training history only. The full assumptions, risks, and safeguards are documented in `docs/outliers.md`.

## Exploratory Data Analysis

`src/eda.py` provides `eda_summary()`, which profiles schema, missingness, unique values, descriptive statistics, medians, skewness, kurtosis, categorical frequencies, numeric correlations, and columns needing attention. The pipeline imports this helper and displays its results before creating a reproducible EDA dashboard under `reports/aapl_eda_overview.png`.

The EDA covers daily-return and absolute-return distributions, volume behavior, intraday range versus absolute return, volume versus absolute return, adjusted close over time, 21-day rolling volatility, and a focused correlation matrix. Results show strongly heavy-tailed absolute returns, intraday ranges, and volume. Intraday range has the strongest contemporaneous relationship with absolute return among the simple diagnostics, while rolling volatility provides meaningful time-local structure. These observations motivate leakage-safe lagged return, range, rolling-volatility, and volume features in Stage 09.

EDA findings remain descriptive. Same-day range cannot be used for a forecast made before that day closes, correlations do not imply causality, full-sample statistics can hide regime shifts, and price levels are non-stationary. Time-aware feature alignment and validation remain mandatory.

## Current Stage

**Exploratory Data Analysis complete.** The pipeline now includes reusable numeric and categorical profiling, attention flags, distributions, bivariate relationships, a time-series view, and correlation analysis. The documented findings lead directly to leakage-safe feature hypotheses for Stage 09.
