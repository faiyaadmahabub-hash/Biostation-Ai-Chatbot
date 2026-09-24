# Generalized Linear Model (Logistic/Poisson)
# Purpose: Model non-normal outcomes

# Load required packages
{package_helper}
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Fit GLM
# family = binomial for binary outcome (logistic regression)
# family = poisson for count data
model <- glm({y_var} ~ {predictors}, family = {family}, data = {data})

# Model summary
cat("=== GLM Results ===\n")
print(summary(model))

# For logistic regression: Odds ratios
if ("{family}" == "binomial") {{
  cat("\n=== Odds Ratios ===\n")
  print(exp(coef(model)))
  cat("\n95% CI for Odds Ratios:\n")
  print(exp(confint(model)))
}}

# Model fit
cat("\nAIC:", AIC(model))
cat("\nNull deviance:", model$null.deviance)
cat("\nResidual deviance:", model$deviance, "\n")
