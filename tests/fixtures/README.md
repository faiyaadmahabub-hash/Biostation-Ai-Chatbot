# Test Fixtures

This directory contains test data and fixtures for BioStation AI tests.

## Structure

- `sample_datasets/` - Sample CSV/Excel files for testing statistical analyses
  - `iris.csv` - Classic Iris dataset (classification, ANOVA)
  - `mtcars.csv` - Motor Trend cars dataset (regression, t-tests)
  - `two_way_anova.csv` - Sample data for two-way ANOVA testing

## Adding New Fixtures

When adding new test datasets:
1. Use realistic but small datasets (< 100 rows preferred)
2. Document the intended use case
3. Include both clean and messy data variations
4. Add fixture loader in `conftest.py` if reused across tests
