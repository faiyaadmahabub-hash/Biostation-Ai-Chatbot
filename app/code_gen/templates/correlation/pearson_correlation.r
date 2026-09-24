# Pearson Correlation
# Purpose: Measure linear relationship between two continuous variables

# Load required packages
{package_helper}
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Perform Pearson correlation test
result <- cor.test({x_var}, {y_var}, method = "pearson")

# Print results
cat("📊 Pearson Correlation\n")
print(result)

cat("\nInterpretation of r:")
cat("\n  |r| < 0.3 = weak")
cat("\n  0.3 ≤ |r| < 0.7 = moderate")
cat("\n  |r| ≥ 0.7 = strong\n")

# Visualization
ggplot({data}, aes(x = {x_var}, y = {y_var})) +
  geom_point(alpha = 0.6) +
  geom_smooth(method = "lm", color = "blue", se = TRUE) +
  labs(title = paste("Pearson r =", round(result$estimate, 3)),
       subtitle = paste("p-value =", format(result$p.value, digits = 3)),
       x = "{x_var_name}", y = "{y_var_name}") +
  theme_minimal()
