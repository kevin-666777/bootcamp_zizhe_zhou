# Stakeholder Memo — AAPL Next-Day Volatility Forecasting

**To:** Portfolio Risk Lead

**From:** Project Team

**Subject:** Scope for an end-of-day AAPL volatility warning prototype

**Decision supported:** Whether AAPL exposure requires an elevated-risk review before the next trading session

## Why This Matters

AAPL exposure can contribute materially to daily portfolio risk, and large moves are difficult to manage if the review process relies only on a static historical average. The proposed project will estimate the magnitude of the next trading day's AAPL return using information available after the current close. The goal is to focus analyst attention on potentially elevated-risk sessions while making the signal's uncertainty and limitations explicit.

## What You Will Receive

- A next-day volatility estimate based initially on absolute close-to-close return
- A comparison with a rolling historical-volatility baseline
- A simple routine-versus-elevated risk indicator with documented thresholds
- A short explanation of important drivers such as recent returns, range, and volume
- Walk-forward MAE/RMSE results and diagnostics for high-volatility periods
- Clear data-quality, regime, and model-limit warnings

## How the Output Supports a Decision

After each close, the risk analyst reviews the forecast and baseline. If forecast risk is elevated, the analyst may inspect position concentration, compare the signal with market context, discuss hedging or exposure limits with the portfolio manager, or increase monitoring for the next session. The prototype will not recommend a direction, select a trade, or execute an order.

## Proposed Success Standard

The model should reduce held-out MAE by a provisional 5% relative to a rolling-volatility baseline and should not achieve that improvement by becoming materially worse on high-volatility days. Results will be measured with time-ordered or walk-forward validation. The threshold is provisional because the available history and baseline variability must first be assessed.

## Assumptions

- Daily OHLCV data are accurate, timely, and consistently adjusted.
- End-of-day features are available before the forecast deadline.
- The initial data history is representative enough to support a classroom prototype.
- Human review remains part of every risk decision.

## Major Risks

- Market regimes may change faster than the model can adapt.
- A short sample may exaggerate correlations or apparent calendar patterns.
- Average metrics may hide failures during tail events.
- Incorrect rolling windows or target alignment can leak future information.
- Forecast improvement may be too small to matter after costs and portfolio context.

## Scope Boundary

The first version covers daily AAPL risk only. It excludes intraday deployment, automated trading, multi-asset portfolio optimization, and causal claims. Options, news, and macroeconomic features are candidates for later versions only if the OHLCV baseline is insufficient and the additional complexity is justified.

## Immediate Next Step

Create the reproducible project environment and configuration, then acquire a longer, versioned AAPL history and confirm the target/baseline definitions before modeling.
