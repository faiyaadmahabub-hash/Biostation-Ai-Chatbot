# Normality Testing
# Purpose: Test if data follows a normal distribution

# Load required packages
{package_helper}
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

cat("=== Normality Tests for {y_var_name} ===\n\n")

# 1. Shapiro-Wilk test (best for n < 5000)
if (length({y_var}) >= 3 & length({y_var}) <= 5000) {{
  shapiro_result <- shapiro.test({y_var})
  cat("📊 Shapiro-Wilk Test\n")
  cat("   W =", round(shapiro_result$statistic, 4), "\n")
  cat("   p-value =", format.pval(shapiro_result$p.value, digits = 4), "\n")

  if (shapiro_result$p.value < 0.05) {{
    cat("   ✗ Data is NOT normally distributed (p < 0.05)\n\n")
  }} else {{
    cat("   ✓ Data appears normally distributed (p ≥ 0.05)\n\n")
  }}
}} else if (length({y_var}) > 5000) {{
  cat("⚠️ Sample size > 5000. Shapiro-Wilk may be too sensitive.\n")
  cat("   Consider visual inspection (Q-Q plot) instead.\n\n")
}}

# 2. Anderson-Darling test (alternative)
ensure_package("nortest")
library(nortest)
ad_result <- ad.test({y_var})
cat("📊 Anderson-Darling Test\n")
cat("   A =", round(ad_result$statistic, 4), "\n")
cat("   p-value =", format.pval(ad_result$p.value, digits = 4), "\n")
if (ad_result$p.value < 0.05) {{
  cat("   ✗ Data is NOT normally distributed (p < 0.05)\n\n")
}} else {{
  cat("   ✓ Data appears normally distributed (p ≥ 0.05)\n\n")
}}

# 3. Descriptive statistics
cat("📈 Descriptive Statistics\n")
cat("   Mean:", round(mean({y_var}, na.rm = TRUE), 3), "\n")
cat("   Median:", round(median({y_var}, na.rm = TRUE), 3), "\n")
cat("   SD:", round(sd({y_var}, na.rm = TRUE), 3), "\n")
ensure_package("moments") # Ensure moments package is loaded for skewness/kurtosis
library(moments)
cat("   Skewness:", round(moments::skewness({y_var}, na.rm = TRUE), 3), "\n")
cat("   Kurtosis:", round(moments::kurtosis({y_var}, na.rm = TRUE), 3), "\n\n")

# 4. Visualization: Q-Q Plot
cat("📊 Generating Q-Q Plot...\n")
qqnorm({y_var}, main = "Q-Q Plot: {y_var_name}")
qqline({y_var}, col = "red", lwd = 2)

# 5. Visualization: Histogram with Normal Curve
x <- {y_var}
hist_data <- data.frame(x = x)

ggplot(hist_data, aes(x = x)) +
  geom_histogram(aes(y = after_stat(density)),
                 bins = 30, fill = "steelblue", alpha = 0.7, color = "white") +
  geom_density(color = "darkblue", linewidth = 1) +
  stat_function(
    fun = dnorm,
    args = list(mean = mean(x, na.rm = TRUE), sd = sd(x, na.rm = TRUE)),
    color = "red", linewidth = 1, linetype = "dashed"
  ) +
  labs(
    title = "Histogram with Normal Overlay",
    subtitle = "Blue = Actual density, Red dashed = Normal distribution",
    x = "{y_var_name}",
    y = "Density"
  ) +
  theme_minimal()

cat("\n💡 Interpretation Guide:\n")
cat("   • If p > 0.05: Data is likely normal\n")
cat("   • If p < 0.05: Data is likely NOT normal\n")
cat("   • Q-Q plot points should fall on the red line if normal\n")
cat("   • Histogram should match the red dashed normal curve\n")
