# Descriptive Statistics
# Purpose: Calculate mean, variance, and summary stats

# Load required packages
{package_helper}
ensure_package("dplyr")
library(dplyr)

# Load your data
{data_loading}

# View data structure
str(data)
summary(data)

# Calculate statistics for specific columns
# Replace column names with your actual variables if needed
stats <- data %>%
  summarise(
    Mean = mean({y_var}, na.rm = TRUE),
    Median = median({y_var}, na.rm = TRUE),
    SD = sd({y_var}, na.rm = TRUE),
    Variance = var({y_var}, na.rm = TRUE),
    Min = min({y_var}, na.rm = TRUE),
    Max = max({y_var}, na.rm = TRUE),
    N = n()
  )

print(stats)

# Visualization: Histogram
hist(data${y_var_clean}, main = "Distribution of {y_var_name}",
     xlab = "{y_var_name}", col = "lightblue", border = "white")
