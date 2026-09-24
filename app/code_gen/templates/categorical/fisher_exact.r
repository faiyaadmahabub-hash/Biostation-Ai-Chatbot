# Fisher's Exact Test
# Purpose: Test association with small sample sizes

# Load required packages
{package_helper}

# Load your data
{data_loading}

# Create contingency table
cont_table <- table({var1}, {var2})
cat("📋 Contingency Table\n")
print(cont_table)

# Perform Fisher's exact test
result <- fisher.test(cont_table)

cat("\n📊 Fisher's Exact Test\n")
print(result)

# Odds ratio interpretation (for 2x2 tables)
if (nrow(cont_table) == 2 & ncol(cont_table) == 2) {{
  cat("\nOdds Ratio:", round(result$estimate, 3))
  cat("\n95% CI:", round(result$conf.int[1], 3), "-", round(result$conf.int[2], 3), "\n")
}}
