# Stage 04 — Data Acquisition and Ingestion

This submission implements a reproducible market-data ingestion workflow. The executed notebook requests recent AAPL daily OHLCV data from Alpha Vantage, with `yfinance` as an assignment-approved fallback, and scrapes the S&P 500 constituents table from Wikipedia using BeautifulSoup. Both datasets are parsed into typed pandas DataFrames, validated for schema and basic data-quality rules, and saved as timestamped CSV files in `data/raw/`. API credentials remain only in a local `.env` file excluded from Git.
