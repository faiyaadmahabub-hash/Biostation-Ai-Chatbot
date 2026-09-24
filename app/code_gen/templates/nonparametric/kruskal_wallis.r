# Kruskal-Wallis Test
# Purpose: Compare 3+ groups (non-parametric)

# Load required packages
{package_helper}
ensure_package("ggplot2")
ensure_package("dunn.test")
library(ggplot2)
library(dunn.test)  # For post-hoc

# Load your data
{data_loading}

# Perform Kruskal-Wallis test
result <- kruskal.test({y_var} ~ {group_var}, data = {data})

# Print results
cat("📊 Kruskal-Wallis Test\n")
print(result)

# Post-hoc: Dunn's test (if significant)
if (result$p.value < 0.05) {{
  cat("\n🔍 Post-hoc: Dunn's Test\n")
  dunn.test({y_var}, {group_var}, method = "bonferroni")

  cat("\n🔸 Holm correction:\n")
  dunn.test({y_var}, {group_var}, method = "holm")

  cat("\n🔸 FDR/BH correction:\n")
  dunn.test({y_var}, {group_var}, method = "bh")
}}

# Summary statistics by group
cat("\n📈 Group Medians\n")
print(aggregate({y_var} ~ {group_var}, data = {data}, FUN = median))

# Visualization
ggplot({data}, aes(x = {group_var}, y = {y_var}, fill = {group_var})) +
  geom_violin(alpha = 0.5) +
  geom_boxplot(width = 0.2, alpha = 0.8) +
  labs(title = "Kruskal-Wallis: Group Comparison") +
  theme_minimal() +
  theme(legend.position = "none")
