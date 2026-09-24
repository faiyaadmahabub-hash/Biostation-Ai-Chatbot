# Spearman Correlation
# Purpose: Measure monotonic relationship (non-parametric)

# Load required packages
{package_helper}
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Perform Spearman correlation test
result <- cor.test({x_var}, {y_var}, method = "spearman")

# Print results
cat("📊 Spearman Correlation\n")
print(result)

# Visualization
ggplot({data}, aes(x = {x_var}, y = {y_var})) +
  geom_point(alpha = 0.6) +
  geom_smooth(method = "loess", color = "purple", se = TRUE) +
  labs(title = paste("Spearman rho =", round(result$estimate, 3)),
       subtitle = paste("p-value =", format(result$p.value, digits = 3)),
       x = "{x_var_name}", y = "{y_var_name}") +
  theme_minimal()
