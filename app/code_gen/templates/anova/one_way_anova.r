# One-Way ANOVA
# Purpose: Compare means across 3+ groups

# Load required packages
{package_helper}
ensure_package("ggplot2")
ensure_package("car")
ensure_package("multcomp")
library(ggplot2)
library(car)        # For Levene's test
library(multcomp)   # For Tukey HSD

# Load your data
{data_loading}

# Check assumptions
cat("🔍 Assumption Checks\n\n")

# 1. Normality (Shapiro-Wilk per group)
cat("Normality by group:\n")
for (grp in unique({group_var})) {{
  subset_data <- {y_var}[{group_var} == grp]
  if (length(subset_data) >= 3 & length(subset_data) <= 5000) {{
    shap <- shapiro.test(subset_data)
    cat("  ", grp, "- p =", round(shap$p.value, 4), "\n")
  }}
}}

# 2. Homogeneity of variances
levene <- leveneTest({y_var} ~ as.factor({group_var}), data = {data})
cat("\nLevene's test p-value:", round(levene$`Pr(>F)`[1], 4), "\n")

# Perform ANOVA
cat("\n📊 ANOVA Results\n")
model <- aov({y_var} ~ {group_var}, data = {data})
print(summary(model))

# Effect size (Eta-squared)
ss_between <- summary(model)[[1]]["Sum Sq"][1,1]
ss_total <- sum(summary(model)[[1]]["Sum Sq"])
eta_sq <- ss_between / ss_total
cat("\nEffect size (Eta-squared):", round(eta_sq, 3), "\n")

# Post-hoc: Tukey's HSD (if ANOVA is significant)
if (summary(model)[[1]]["Pr(>F)"][1,1] < 0.05) {{
  cat("\n🔍 Post-hoc: Tukey's HSD\n")
  tukey <- TukeyHSD(model)
  print(tukey)

  cat("\n2️⃣ Pairwise t-tests with corrections\n\n")

  cat("🔸 Bonferroni (most conservative):\n")
  bonf_p <- pairwise.t.test({y_var}, {group_var}, p.adjust.method = "bonferroni", pool.sd = TRUE)
  print(round(bonf_p$p.value, 4))

  cat("\n🔸 Holm (sequential Bonferroni):\n")
  holm_p <- pairwise.t.test({y_var}, {group_var}, p.adjust.method = "holm", pool.sd = TRUE)
  print(round(holm_p$p.value, 4))

  cat("\n🔸 FDR/Benjamini-Hochberg:\n")
  fdr_p <- pairwise.t.test({y_var}, {group_var}, p.adjust.method = "fdr", pool.sd = TRUE)
  print(round(fdr_p$p.value, 4))

  cat("\n💡 Bonferroni=conservative, FDR=exploratory\n")
}}

# Visualization
ggplot({data}, aes(x = {group_var}, y = {y_var}, fill = {group_var})) +
  geom_boxplot(alpha = 0.7) +
  geom_jitter(width = 0.2, alpha = 0.4) +
  stat_summary(fun = mean, geom = "point", shape = 18, size = 4, color = "red") +
  labs(title = "Comparison Across Groups",
       subtitle = "Boxes show median/IQR, red diamonds show means",
       x = "{group_var_name}", y = "{y_var_name}") +
  theme_minimal() +
  theme(legend.position = "none")
