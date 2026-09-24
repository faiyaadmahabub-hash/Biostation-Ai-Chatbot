# Linear Regression
# Purpose: Model relationship between outcome and predictors

# Load required packages
{package_helper}
ensure_package("ggplot2")
ensure_package("car")
library(ggplot2)
library(car)  # For diagnostic plots

# Load your data
{data_loading}

# Fit linear model
model <- lm({y_var} ~ {predictors}, data = {data})

# Model summary
cat("=== Linear Regression Results ===\n")
print(summary(model))

# Confidence intervals for coefficients
cat("\n=== 95% Confidence Intervals ===\n")
print(confint(model))

# Model diagnostics
cat("\n=== Diagnostic Checks ===\n")
cat("Checking: Linearity, Normality of residuals, Homoscedasticity\n")

# Diagnostic plots
par(mfrow = c(2, 2))
plot(model)
par(mfrow = c(1, 1))

# VIF for multicollinearity (if multiple predictors)
if (length(attr(terms(model), "term.labels")) > 1) {{
  cat("\n=== Variance Inflation Factors ===\n")
  print(vif(model))
  cat("VIF > 5 suggests multicollinearity concern\n")
}}
