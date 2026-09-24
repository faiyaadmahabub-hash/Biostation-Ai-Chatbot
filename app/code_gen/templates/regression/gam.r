# Generalized Additive Model (GAM)
# Purpose: Model non-linear relationships using smooth functions

# Load required packages
{package_helper}
ensure_package("mgcv")
library(mgcv)

# Load your data
{data_loading}

# Fit GAM with smooth terms
# s() creates smooth functions
# k = basis dimension (lower = smoother, higher = more flexible)
model <- gam({y_var} ~ s({smooth_var}, k = 10),
              data = {data})

# Model summary
cat("=== GAM Results ===\n")
print(summary(model))

cat("\n📈 Interpreting edf (effective degrees of freedom):\n")
cat("  edf ≈ 1: Linear relationship\n")
cat("  edf > 1: Non-linear relationship\n")
cat("  Higher edf = more complex curve\n\n")

# Model fit statistics
cat("R-squared (adjusted):", round(summary(model)$r.sq, 3), "\n")
cat("Deviance explained:", round(summary(model)$dev.expl * 100, 1), "%\n")
cat("AIC:", round(AIC(model), 2), "\n\n")

# Check for concurvity (GAM's version of multicollinearity)
cat("=== Concurvity Check ===\n")
print(concurvity(model, full = TRUE))
cat("Values close to 1 suggest high concurvity\n\n")

# Visualize smooth terms
cat("=== Smooth Term Visualization ===\n")
plot(model, residuals = TRUE, pch = 1, cex = 0.5)

# Diagnostic plots
par(mfrow = c(2, 2))
gam.check(model)
par(mfrow = c(1, 1))
