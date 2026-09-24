# R Code Templates

This directory contains R code templates for statistical tests. Templates are stored as separate `.r` files for better maintainability and syntax highlighting.

## Structure

```
templates/
├── helpers/
│   └── package_installer.r     # Shared package installation function
├── ttests/
│   ├── one_sample_ttest.r
│   ├── unpaired_ttest.r        # ✅ Extracted
│   └── paired_ttest.r
├── anova/
│   ├── one_way_anova.r         # ✅ Extracted
│   └── two_way_anova.r
├── nonparametric/
│   ├── mann_whitney.r
│   ├── wilcoxon_signed_rank.r
│   └── kruskal_wallis.r
├── correlation/
│   ├── pearson_correlation.r
│   └── spearman_correlation.r
├── categorical/
│   ├── chi_squared.r
│   └── fisher_exact.r
├── regression/
│   ├── linear_regression.r
│   ├── glm.r
│   ├── glmm.r
│   └── gam.r
├── survival/
│   ├── kaplan_meier.r
│   └── cox_regression.r
└── diagnostics/
    ├── normality_test.r
    └── descriptive.r
```

## Template Syntax

Templates use `{variable_name}` for placeholders:

```r
# Example template
{package_helper}               # Shared package installer
library(ggplot2)

{data_loading}                 # Automated data loading code

result <- t.test({y_var} ~ {group_var}, data = {data})

cat("Analysis of {y_var_name} by {group_var_name}\n")
```

## Available Variables

Common placeholders used in templates:

- `{package_helper}` - Package installation helper code
- `{data_loading}` - Data loading code (CSV/Excel)
- `{data}` - Data frame name (usually "data")
- `{y_var}` - Dependent variable (e.g., `data$height`)
- `{y_var_name}` - Human-readable name (e.g., "Height")
- `{y_var_clean}` - Variable without prefix (e.g., "height")
- `{x_var}`, `{x_var_name}`, `{x_var_clean}` - Independent variable
- `{group_var}`, `{group_var_name}`, `{group_var_clean}` - Grouping variable
- `{before_var}`, `{after_var}` - For paired tests
- `{predictors}` - Regression predictors
- `{mu}` - Hypothesized mean (one-sample t-test)
- `{family}` - GLM family (binomial, poisson, etc.)

## Adding New Templates

1. Create a new `.r` file in the appropriate directory
2. Add placeholders using `{variable_name}` syntax
3. Update `TEMPLATE_MAP` in `template_loader.py`
4. Test with sample data

## Benefits

✅ **Better editing** - Syntax highlighting in R files
✅ **Easier testing** - Test R code independently
✅ **Cleaner diffs** - Version control tracks R changes separately
✅ **Simpler debugging** - Find errors in R code quickly
✅ **Modular** - Reuse shared components (helpers)

## Migration Status

### ✅ ALL 20 TEMPLATES EXTRACTED (100% COMPLETE!)

**T-Tests:**
- ✅ `one_sample_ttest.r` - One-sample t-test
- ✅ `paired_ttest.r` - Paired t-test
- ✅ `unpaired_ttest.r` - Independent samples t-test

**ANOVA:**
- ✅ `one_way_anova.r` - One-way ANOVA with multiple comparison corrections
- ✅ `two_way_anova.r` - Two-way ANOVA with post-hoc corrections

**Non-Parametric:**
- ✅ `mann_whitney.r` - Mann-Whitney U test
- ✅ `wilcoxon_signed_rank.r` - Wilcoxon signed-rank test
- ✅ `kruskal_wallis.r` - Kruskal-Wallis test

**Correlation:**
- ✅ `pearson_correlation.r` - Pearson correlation
- ✅ `spearman_correlation.r` - Spearman correlation

**Categorical:**
- ✅ `chi_squared.r` - Chi-squared test
- ✅ `fisher_exact.r` - Fisher's exact test

**Regression:**
- ✅ `linear_regression.r` - Linear regression
- ✅ `glm.r` - Generalized linear models
- ✅ `glmm.r` - Generalized linear mixed models
- ✅ `gam.r` - Generalized additive models

**Survival Analysis:**
- ✅ `kaplan_meier.r` - Kaplan-Meier survival curves
- ✅ `cox_regression.r` - Cox proportional hazards

**Diagnostics:**
- ✅ `normality_test.r` - Normality testing
- ✅ `descriptive.r` - Descriptive statistics
