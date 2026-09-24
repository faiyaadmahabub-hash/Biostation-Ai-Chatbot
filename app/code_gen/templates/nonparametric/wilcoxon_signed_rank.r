# Wilcoxon Signed-Rank Test
# Purpose: Compare paired samples (non-parametric)

# Load required packages
{package_helper}
ensure_package("ggplot2")
ensure_package("tidyr")
library(ggplot2)
library(tidyr)

# Load your data
{data_loading}

# Perform Wilcoxon signed-rank test
result <- wilcox.test({before_var}, {after_var}, paired = TRUE)

# Print results
cat("📊 Wilcoxon Signed-Rank Test\n")
print(result)

# Median of differences
differences <- {after_var} - {before_var}
cat("\nMedian difference:", median(differences), "\n")

# Visualization
plot_data <- data.frame(
  Before = {before_var},
  After = {after_var}
) |> pivot_longer(cols = everything(), names_to = "Time", values_to = "Value")

ggplot(plot_data, aes(x = Time, y = Value, fill = Time)) +
  geom_boxplot(alpha = 0.7) +
  labs(title = "Wilcoxon Signed-Rank: Before vs After") +
  theme_minimal()
