# Model Evaluation, Assumptions, and Risk Controls

## Evaluation question

Does the time-aware regression improve next-day AAPL absolute-return forecasts relative to a 21-session rolling-volatility baseline, and does that improvement remain credible on the high-volatility days most relevant to a portfolio risk analyst?

The evidence consists of 1,047 walk-forward forecasts from 2022-06-21 through 2026-08-21. Every observation after the 600-row initial history is forecast exactly once. Model selection, scaling, fitting, and the 80th-percentile tail threshold use only information available before each fold's test window.

## Performance and uncertainty

| Scenario | Observations | Regression MAE | Baseline MAE | Improvement | Preferred paired 95% CI |
|---|---:|---:|---:|---:|---:|
| All forecasts | 1,047 | 0.008505 | 0.009971 | 14.70% | [-0.002183, -0.000924] |
| Ordinary volatility | 921 | 0.006749 | 0.008639 | 21.88% | [-0.002786, -0.001179] |
| Training-defined high volatility | 126 | 0.021342 | 0.019707 | -8.30% | [0.000378, 0.002900] |

The interval estimand is regression absolute error minus baseline absolute error, so negative values favor regression. The table uses the 20-session circular moving-block bootstrap with 5,000 seeded resamples. Gaussian and IID-bootstrap scenarios produce the same signs: all-day and ordinary-day intervals remain below zero, while the tail interval remains above zero. The block interval is preferred because daily forecast errors can cluster, but its block length is an assumption rather than a learned truth.

Calendar-year improvement is positive in every observed subgroup: 13.83% in 2022, 7.80% in 2023, 8.93% in 2024, 21.49% in 2025, and 17.71% in 2026. These subgroups show that the average gain is not confined to one year. They do not establish future stability, and the partial 2022 and 2026 samples are not directly comparable with full years.

## Scenario conclusions

- **Routine monitoring:** Regression produces materially lower ordinary-day MAE and may provide a more focused average-risk estimate.
- **Shock monitoring:** Regression systematically underpredicts large moves and is worse than the simple baseline on the training-defined tail. This is a failed risk requirement, not a minor diagnostic footnote.
- **Interval assumption:** Gaussian and IID bootstrap intervals are narrower because they ignore time dependence. Moving-block resampling widens uncertainty but does not change the decision.
- **Model-selection stability:** Ridge with `alpha=100` was selected in four folds and OLS in two. Coefficients and regularization strength are not permanent market relationships.

## Key assumptions and limitations

1. Historical adjusted OHLCV data are accurate, timely, and consistently revised.
2. Current-close features are available before the next-session decision cutoff.
3. An expanding history remains relevant despite regime change.
4. A 21-session return standard deviation is an appropriate transparent comparator for next-day absolute return.
5. The 80th percentile of each training target is a useful operational tail definition.
6. A 20-session block captures enough short-run error dependence for sensitivity analysis.
7. Absolute return is a useful volatility proxy even though it omits intraday paths and portfolio-specific exposure.

Gaussian intervals additionally assume an approximately normal mean and independent observations. IID bootstrap relaxes normality but assumes exchangeable days. Circular moving-block bootstrap preserves local order but joins the end of a sample to its beginning. For the sparse tail subset, neighboring resampled observations are neighboring tail events, not necessarily consecutive sessions. None of the intervals includes uncertainty from vendor revisions, feature choice, repeated model selection beyond the executed procedure, transaction costs, position size, or hedging effectiveness.

## Decision boundary

The model is **advisory only**. It passes the provisional 5% average-MAE improvement threshold but fails the paired tail-performance safeguard. The analyst may use it alongside the baseline to prioritize routine review, but must retain the baseline, concentration context, and human judgment for elevated-risk decisions. It must not automatically trade, hedge, change limits, or suppress an alert.

Operational acceptance would require a new model or ensemble to maintain a below-zero paired-error interval overall **and** avoid materially worse training-defined tail MAE across multiple recent windows. Any change to the target, threshold, features, window length, or data source requires time-ordered reevaluation.

## Production monitoring requirements

- **Input controls:** source freshness, schema/dtype checks, duplicate dates, missingness, invalid OHLCV relationships, and adjustment anomalies.
- **Drift:** feature range/distribution shifts, forecast distribution, target distribution after realization, and observations outside training ranges.
- **Performance:** rolling paired MAE/RMSE, model-versus-baseline win rate, moving-block interval, year/regime subgroup metrics, and residual mean/clusters.
- **Tail risk:** tail MAE, underprediction magnitude, missed elevated events, alert frequency, and concentration-aware analyst overrides.
- **Triggers:** stale or invalid data; a sustained non-negative all-day paired interval; materially worse tail MAE; clustered large residuals; or a regime outside historical coverage.
- **Governance:** logged forecasts and inputs, reproducible model/version metadata, human sign-off, scheduled review, and time-ordered revalidation before retraining or deployment.
