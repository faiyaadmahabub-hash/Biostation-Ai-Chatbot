# One-Sample T-Test
# Purpose: Compare sample mean to a known value

# Load required packages
{package_helper}
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Check normality (optional but recommended)
shapiro_test <- shapiro.test({y_var})
cat("Shapiro-Wilk normality test p-value:", shapiro_test$p.value, "\n")
if (shapiro_test$p.value < 0.05) {{
  cat("Warning: Data may not be normally distributed. Consider Wilcoxon test.\n")
}}

# Perform one-sample t-test
# H0: Mean = {mu} (hypothesized value)
result <- t.test({y_var}, mu = {mu})

# Print results
print(result)

# Calculate effect size (Cohen's d)
cohens_d <- (mean({y_var}) - {mu}) / sd({y_var})
cat("\nEffect size (Cohen's d):", round(cohens_d, 3), "\n")

# Visualization
ggplot(data.frame(x = {y_var}), aes(x = x)) +
  geom_histogram(aes(y = after_stat(density)), bins = 20, fill = "steelblue", alpha = 0.7) +
  geom_density(color = "darkblue", linewidth = 1) +
  geom_vline(xintercept = {mu}, color = "red", linetype = "dashed", linewidth = 1) +
  geom_vline(xintercept = mean({y_var}), color = "green", linewidth = 1) +
  labs(title = "Distribution of {y_var_name}",
       subtitle = paste("Sample mean (green) vs. Hypothesized (red):", {mu}),
       x = "{y_var_name}", y = "Density") +
  theme_minimal()
