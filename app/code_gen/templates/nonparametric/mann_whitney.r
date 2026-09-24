# Mann-Whitney U Test (Wilcoxon Rank-Sum)
# Purpose: Compare two independent groups (non-parametric)

# Load required packages
{package_helper}
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Perform Mann-Whitney U test
result <- wilcox.test({y_var} ~ {group_var}, data = {data})

# Print results
cat("📊 Mann-Whitney U Test\n")
print(result)

# Effect size (r = Z / sqrt(N))
# Approximate calculation
n <- length({y_var})
z <- qnorm(result$p.value / 2)
effect_r <- abs(z) / sqrt(n)
cat("\nEffect size (r):", round(effect_r, 3))
cat("\nInterpretation: small=0.1, medium=0.3, large=0.5\n")

# Summary statistics by group
cat("\n📈 Group Medians\n")
print(aggregate({y_var} ~ {group_var}, data = {data}, FUN = median))

# Visualization
ggplot({data}, aes(x = {group_var}, y = {y_var}, fill = {group_var})) +
  geom_violin(alpha = 0.5) +
  geom_boxplot(width = 0.2, alpha = 0.8) +
  labs(title = "Mann-Whitney U Test: Comparison",
       x = "{group_var_name}", y = "{y_var_name}") +
  theme_minimal() +
  theme(legend.position = "none")
