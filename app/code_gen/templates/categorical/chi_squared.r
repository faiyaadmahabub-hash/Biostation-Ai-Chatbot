# Chi-Squared Test of Independence
# Purpose: Test association between two categorical variables

# Load required packages
{package_helper}
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Create contingency table
cont_table <- table({var1}, {var2})
cat("📋 Contingency Table\n")
print(cont_table)

# Check expected frequencies
expected <- chisq.test(cont_table)$expected
cat("\n🎲 Expected Frequencies\n")
print(round(expected, 1))
if (any(expected < 5)) {{
  cat("\nWarning: Some expected frequencies < 5. Consider Fisher's exact test.\n")
}}

# Perform chi-squared test
result <- chisq.test(cont_table)

cat("\n📊 Chi-Squared Test\n")
print(result)

# Effect size (Cramer's V)
n <- sum(cont_table)
min_dim <- min(nrow(cont_table), ncol(cont_table)) - 1
cramers_v <- sqrt(result$statistic / (n * min_dim))
cat("\nEffect size (Cramer's V):", round(cramers_v, 3))
cat("\nInterpretation: small=0.1, medium=0.3, large=0.5\n")

# Visualization
mosaicplot(cont_table, main = "Mosaic Plot", color = TRUE)
