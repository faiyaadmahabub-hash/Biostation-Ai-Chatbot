# Generalized Linear Mixed Model (GLMM)
# Purpose: Model non-normal data with random effects for non-independent observations

# Load required packages
{package_helper}
ensure_package("lme4")
ensure_package("lmerTest")
library(lme4)
library(lmerTest)

# Load your data
{data_loading}

# Fit GLMM
# For binary outcome: family = binomial
# For count data: family = poisson
# (1|{random_var}) = random intercept for {random_var}
model <- glmer({y_var} ~ {fixed_effects} + (1|{random_var}),
                 family = {family},
                 data = {data})

# Model summary
cat("=== GLMM Results ===\n")
print(summary(model))

# Random effects variance
cat("\n=== Random Effects ===\n")
print(VarCorr(model))

# Fixed effects confidence intervals
cat("\n=== 95% CI for Fixed Effects ===\n")
print(confint(model, parm = "beta_"))

# For logistic GLMM: Odds ratios
if ("{family}" == "binomial") {{
  cat("\n=== Odds Ratios ===\n")
  fixed_effects <- fixef(model)
  print(exp(fixed_effects))
}}

# Model diagnostics
cat("\n=== Model Diagnostics ===\n")
cat("AIC:", AIC(model), "\n")
cat("BIC:", BIC(model), "\n")

# Residual plots
plot(model)
