# Paired T-Test
# Purpose: Compare means from paired/matched observations

# Load required packages
{package_helper}
ensure_package("ggplot2")
ensure_package("tidyr")
library(ggplot2)
library(tidyr)

# Load your data
{data_loading}

# Calculate differences
differences <- {after_var} - {before_var}

# Check normality of differences
shapiro_test <- shapiro.test(differences)
cat("Shapiro-Wilk test on differences p-value:", shapiro_test$p.value, "\n")
if (shapiro_test$p.value < 0.05) {{
  cat("Warning: Differences may not be normal. Consider Wilcoxon signed-rank test.\n")
}}

# Perform paired t-test
result <- t.test({before_var}, {after_var}, paired = TRUE)

# Print results
print(result)

# Effect size (Cohen's d for paired data)
cohens_d <- mean(differences) / sd(differences)
cat("\nEffect size (Cohen's d):", round(cohens_d, 3), "\n")

# Visualization - Before/After plot
plot_data <- data.frame(
  id = 1:length({before_var}),
  Before = {before_var},
  After = {after_var}
) |> pivot_longer(cols = c(Before, After), names_to = "Time", values_to = "Value")

ggplot(plot_data, aes(x = Time, y = Value, group = id)) +
  geom_line(alpha = 0.3) +
  geom_point(aes(color = Time), size = 3) +
  stat_summary(aes(group = 1), fun = mean, geom = "line", color = "red", linewidth = 1.5) +
  stat_summary(aes(group = 1), fun = mean, geom = "point", color = "red", size = 4) +
  labs(title = "Before vs After Comparison",
       subtitle = "Individual pairs (gray) and mean (red)") +
  theme_minimal()
