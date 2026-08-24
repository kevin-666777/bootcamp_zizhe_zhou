# Outlier Policy for AAPL Daily Returns

## Definition and decision

The project defines a daily return outlier using the adjusted-close return distribution and the IQR rule: values below `Q1 - 1.5 × IQR` or above `Q3 + 1.5 × IQR` are flagged. IQR is the primary method because financial returns are heavy-tailed and often violate the normality assumption behind Z-scores. A three-standard-deviation Z-score flag is retained as a comparison, while 1st/99th-percentile winsorization is used only for sensitivity analysis.

Outliers are **flagged, not deleted from the canonical cleaned dataset**. Large price movements are often genuine risk events and are central to a next-day volatility project. The pipeline saves an analytical copy containing daily return, absolute daily return, IQR and Z-score flags, then compares statistics for all observations, IQR-filtered observations, and winsorized observations.

## Assumptions

- Adjusted close is the consistent price basis for daily returns because it accounts for splits and dividends.
- The IQR threshold is a transparent screening convention, not proof that an observation is erroneous.
- A global threshold provides a simple Stage 07 diagnostic but may behave differently across volatility regimes.
- The first return is missing by construction and is not an outlier.
- Winsorization changes values and is therefore not applied to the saved canonical return column.

## Risks and safeguards

- Removing genuine crash or rally days would understate tail risk and may make later model metrics look artificially good. The default workflow keeps every validated market row and uses flags for stratified evaluation.
- Vendor errors can resemble true market shocks. Flagged dates should be checked against prices, corporate actions, and an independent source before being classified as bad data.
- IQR may label many valid observations when returns are strongly skewed or regime-dependent. Later evaluation should compare calm and volatile periods and consider rolling thresholds fitted only on past data.
- A global threshold uses the full sample and must not become a predictive feature in time-ordered modeling. It is an EDA/audit annotation; any production-time threshold must be estimated on training history only.
- Winsorized sensitivity results show how conclusions depend on tail magnitude, but winsorized data should not replace raw outcomes without stakeholder approval and explicit reporting.
