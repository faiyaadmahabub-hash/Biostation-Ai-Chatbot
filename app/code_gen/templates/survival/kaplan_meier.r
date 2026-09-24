# Kaplan-Meier Survival Analysis
# Purpose: Estimate survival probabilities over time

# Load required packages
{package_helper}
ensure_package("survival")
ensure_package("survminer")
library(survival)
library(survminer)

# Load your data
{data_loading}

# Create survival object
# time_var = time to event or censoring
# event_var = 1 if event occurred, 0 if censored
surv_obj <- Surv(time = {time_var}, event = {event_var})

# Fit Kaplan-Meier curves
km_fit <- survfit(surv_obj ~ {group_var}, data = {data})

# Print summary
cat("=== Kaplan-Meier Survival Analysis ===\n")
print(km_fit)

# Median survival times
cat("\n=== Median Survival Times ===\n")
print(summary(km_fit)$table)

# Log-rank test (compare survival curves between groups)
cat("\n=== Log-Rank Test ===\n")
logrank_test <- survdiff(surv_obj ~ {group_var}, data = {data})
print(logrank_test)

if (logrank_test$pvalue < 0.05) {{
  cat("\n✓ Significant difference in survival between groups (p < 0.05)\n")
}} else {{
  cat("\n✗ No significant difference in survival between groups (p ≥ 0.05)\n")
}}

# Survival curve plot
ggsurvplot(
  km_fit,
  data = {data},
  pval = TRUE,
  conf.int = TRUE,
  risk.table = TRUE,
  risk.table.col = "strata",
  linetype = "strata",
  surv.median.line = "hv",
  ggtheme = theme_minimal(),
  title = "Kaplan-Meier Survival Curves",
  xlab = "Time",
  ylab = "Survival Probability"
)
