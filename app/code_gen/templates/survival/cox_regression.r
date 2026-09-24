# Cox Proportional Hazards Regression
# Purpose: Model time-to-event data with covariates

# Load required packages
{package_helper}
ensure_package("survival")
ensure_package("survminer")
library(survival)
library(survminer)

# Load your data
{data_loading}

# Create survival object
surv_obj <- Surv(time = {time_var}, event = {event_var})

# Fit Cox regression model
cox_model <- coxph(surv_obj ~ {predictors}, data = {data})

# Model summary
cat("=== Cox Proportional Hazards Regression ===\n")
print(summary(cox_model))

# Hazard ratios with confidence intervals
cat("\n=== Hazard Ratios ===\n")
hr <- exp(coef(cox_model))
hr_ci <- exp(confint(cox_model))
hr_table <- cbind(HR = hr, hr_ci)
print(round(hr_table, 3))

cat("\n📊 Interpreting Hazard Ratios:\n")
cat("  HR = 1: No effect\n")
cat("  HR > 1: Increased hazard (worse survival)\n")
cat("  HR < 1: Decreased hazard (better survival)\n\n")

# Test proportional hazards assumption
cat("=== Proportional Hazards Assumption Test ===\n")
ph_test <- cox.zph(cox_model)
print(ph_test)

if (any(ph_test$table[,"p"] < 0.05)) {{
  cat("\n⚠️ Warning: Proportional hazards assumption may be violated (p < 0.05)\n")
  cat("   Consider stratification or time-varying coefficients\n")
}} else {{
  cat("\n✓ Proportional hazards assumption satisfied (p ≥ 0.05)\n")
}}

# Plot Schoenfeld residuals
plot(ph_test)

# Forest plot of hazard ratios
ggforest(cox_model, data = {data})
