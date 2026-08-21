# Stage 05 — Data Storage

This submission implements a reusable, environment-driven storage layer for a small AAPL sample dataset. The executed notebook creates the DataFrame, saves it in two formats, reloads both copies, and validates their shapes, columns, critical data types, and values. Reusable routing functions live in `src/storage.py`.

## Data Storage

### Folder structure

- `data/raw/` stores the CSV snapshot. CSV is human-readable, easy to inspect, and widely compatible, making it appropriate for a raw interchange copy.
- `data/processed/` stores the Parquet copy. Parquet is compressed, column-oriented, and preserves pandas data types more faithfully, making it appropriate for efficient downstream analysis.

### Environment-driven paths

The local `.env` defines `DATA_DIR_RAW=data/raw` and `DATA_DIR_PROCESSED=data/processed`. The Notebook loads these variables with `python-dotenv` and resolves them relative to the Stage 05 project directory. The `.env` file is excluded from Git; `.env.example` documents the expected variables with safe placeholder values.

### Read/write utilities

`write_df(df, path)` and `read_df(path)` choose CSV or Parquet behavior from the file suffix. The writer creates missing parent directories automatically. The reader raises a clear `FileNotFoundError` for missing files, parses common CSV date columns, and both functions provide an actionable message when a Parquet engine is unavailable. Supported suffixes are `.csv`, `.parquet`, `.pq`, and `.parq`.

### Validation

After reloading, the Notebook checks that CSV and Parquet copies have the same shape and columns as the original. It also checks the `date`, `ticker`, `price`, and `volume` dtypes and compares their values. The validation results are displayed as a compact checklist.
