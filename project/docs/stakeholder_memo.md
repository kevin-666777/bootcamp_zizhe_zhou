# Stakeholder Memo — AAPL Next-Day Volatility Forecasting

**To:** Portfolio Risk Lead

**From:** Project Team

**Subject:** Evaluation decision for the end-of-day AAPL volatility prototype

**Decision supported:** Whether AAPL exposure requires an elevated-risk review before the next trading session

## Why This Matters

AAPL exposure can contribute materially to daily portfolio risk, and large moves are difficult to manage if the review process relies only on a static historical average. This prototype estimates the magnitude of the next trading day's AAPL return using information available after the current close. Its goal is to focus analyst attention on potentially elevated-risk sessions while making the signal's uncertainty and limitations explicit.

## Evaluation Result

Across 1,047 walk-forward forecasts, the regression reduced average MAE from 0.009971 to 0.008505, a 14.70% improvement. A 20-session moving-block bootstrap places the paired daily improvement between 0.000924 and 0.002183 absolute-return units with 95% confidence under that resampling assumption. Average MAE improved in every observed calendar-year subgroup.

The result reverses on the days that matter most for shock risk. On 126 high-volatility observations defined from prior training history, regression MAE was 0.021342 versus 0.019707 for the baseline—8.30% worse. The paired 95% block-bootstrap interval also favors the baseline in this scenario. The model therefore passes the average-error target but fails the tail-risk safeguard.

## How the Output Supports a Decision

After each close, the analyst may use the regression to prioritize routine review, but must view it beside the 21-day baseline. If either signal is elevated—or if position concentration or market context creates concern—the analyst escalates for human review. The regression must not suppress a baseline warning, recommend direction, select a trade, change a limit, or execute an order.

## Acceptance Decision

**Not approved for automated risk action.** The model exceeded the provisional 5% average-MAE improvement threshold but became materially worse on training-defined high-volatility days. It remains an educational, advisory prototype. Approval would require sustained average improvement without tail deterioration across multiple recent time-ordered windows.

## Assumptions Behind the Result

- Daily OHLCV data are accurate, timely, and consistently adjusted.
- End-of-day features are available before the forecast deadline.
- Expanding historical data remain relevant despite market regime changes.
- A 20-session bootstrap block reasonably reflects short-run error dependence.
- Training-period 80th-percentile absolute return is a useful tail definition.
- Human review remains part of every risk decision.

## Major Risks

- Market regimes may change faster than the model can adapt.
- A short sample may exaggerate correlations or apparent calendar patterns.
- Average metrics hide the observed failure during tail events.
- Incorrect rolling windows or target alignment can leak future information.
- Forecast improvement may be too small to matter after costs and portfolio context.

## Scope Boundary

The first version covers daily AAPL risk only. It excludes intraday deployment, automated trading, multi-asset portfolio optimization, and causal claims. Options, news, and macroeconomic features are candidates for later versions only if the OHLCV baseline is insufficient and the additional complexity is justified.

## Monitoring Required Before Any Live Use

Track data freshness and schema, feature drift, rolling paired MAE/RMSE, block-bootstrap intervals, residual clusters, tail MAE and underprediction, model-versus-baseline win rate, and alert frequency. Trigger review on stale data, a sustained loss of average improvement, materially worse tail performance, or a regime outside training coverage. Any retraining or feature change requires time-ordered revalidation and human approval.
