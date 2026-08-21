# Stage 06 — Data Preprocessing

This submission turns the lecture's fill, drop, and scale patterns into reusable functions in `src/cleaning.py`. The executed preprocessing notebook loads the provided sample dataset from `data/raw/`, applies the cleaning pipeline, compares the original and cleaned data, documents tradeoffs, and saves the result to `data/processed/sample_data_cleaned.csv`.

## Cleaning Strategy

1. **Median imputation:** Missing values in `age`, `income`, and `score` are filled with each column's median. Median imputation is simple and less sensitive to extreme values than mean imputation, but it reduces natural variation and may hide meaningful missingness.
2. **Drop high-missingness columns:** Columns with more than 50% missing values are removed. This drops `extra_data`, which is missing in five of seven rows. The function defaults to columns because preserving the small dataset's observations is more useful than discarding rows.
3. **Min-max normalization:** `age`, `income`, and `score` are scaled to the `[0, 1]` range. This puts differently scaled numeric features on a common range, although the resulting values depend on the observed minimum and maximum and can be sensitive to future outliers.

`zipcode` is explicitly loaded as text because it is an identifier, not a quantity. `city` and `zipcode` are not normalized. Every cleaning function returns a copy rather than mutating its input, validates requested columns or parameters, and includes a docstring. The processed CSV contains no missing values for this sample dataset.
