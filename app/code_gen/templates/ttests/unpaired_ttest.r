# Independent Samples T-Test (Unpaired)
# Purpose: Compare means between two independent groups

# Load required packages
{package_helper}
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Check normality in each group
cat("Checking normality:\n")
for (grp in unique({group_var})) {{
  subset_data <- {y_var}[{group_var} == grp]
  if (length(subset_data) >= 3) {{
    shap <- shapiro.test(subset_data)
    cat("  Group", grp, "- Shapiro p-value:", round(shap$p.value, 4), "\n")
  }}
}}

# Check homogeneity of variances
var_test <- var.test({y_var} ~ {group_var}, data = {data})
cat("\nLevene's test for equal variances p-value:", round(var_test$p.value, 4), "\n")

# Perform independent samples t-test
# Using Welch's t-test (default, doesn't assume equal variances)
result <- t.test({y_var} ~ {group_var}, data = {data})

# Print results
print(result)

# Effect size (Cohen's d)
group_levels <- unique({group_var})
g1 <- {y_var}[{group_var} == group_levels[1]]
g2 <- {y_var}[{group_var} == group_levels[2]]
pooled_sd <- sqrt(((length(g1)-1)*sd(g1)^2 + (length(g2)-1)*sd(g2)^2) / (length(g1)+length(g2)-2))
cohens_d <- (mean(g1) - mean(g2)) / pooled_sd
cat("\nEffect size (Cohen's d):", round(cohens_d, 3), "\n")

# Visualization
ggplot({data}, aes(x = {group_var}, y = {y_var}, fill = {group_var})) +
  geom_boxplot(alpha = 0.7) +
  geom_jitter(width = 0.2, alpha = 0.5) +
  labs(title = "Comparison of {y_var_name} by {group_var_name}",
       x = "{group_var_name}", y = "{y_var_name}") +
  theme_minimal() +
  theme(legend.position = "none")
