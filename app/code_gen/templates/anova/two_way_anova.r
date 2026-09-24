# Two-Way ANOVA
# Purpose: Compare means across groups defined by two factors
# Factor 1: {x_var_name}
# Factor 2: {group_var_name}

# Load required packages
{package_helper}
ensure_package("ggplot2")
ensure_package("car")
ensure_package("emmeans")
library(ggplot2)
library(car)
library(emmeans)  # For post-hoc tests with corrections

# Load your data
{data_loading}

# Check class of factors (ensure they are factors)
data${x_var_clean} <- as.factor(data${x_var_clean})
data${group_var_clean} <- as.factor(data${group_var_clean})

# Check assumptions
cat("🔍 Assumption Checks\n\n")

# 1. Homogeneity of variances (Levene's Test)
# We test if variance differs across all combinations of groups
levene_result <- leveneTest({y_var} ~ {x_var} * {group_var}, data = {data})
cat("Levene's Test p-value:", round(levene_result$`Pr(>F)`[1], 4), "\n")
if(levene_result$`Pr(>F)`[1] < 0.05) {{
  cat("⚠️ Warning: Variances are not equal (p < 0.05)\n")
}} else {{
  cat("✓ Assumption met: Variances are equal\n")
}}

# Perform Two-Way ANOVA
# Using Type II Sum of Squares (safer for unbalanced designs)
cat("\n📊 Two-Way ANOVA Results (Type II SS)\n")
model <- lm({y_var} ~ {x_var} * {group_var}, data = {data})
anova_results <- Anova(model, type = "II")
print(anova_results)

# Calculate Partial Eta-Squared (Effect Size)
ss <- anova_results$"Sum Sq"
sse <- ss[length(ss)] # Residual SS
eta_sq <- ss / (ss + sse)
cat("\nEffect Sizes (Partial Eta-Squared):\n")
eta_table <- data.frame(Term = rownames(anova_results), Partial_Eta_Sq = round(eta_sq, 3))
print(eta_table[1:(nrow(eta_table)-1), ]) # Exclude residuals

# ============================================================
# POST-HOC TESTS WITH MULTIPLE COMPARISON CORRECTIONS
# ============================================================

cat("\n" , paste(rep("=", 60), collapse=""), "\n")
cat("📊 POST-HOC PAIRWISE COMPARISONS\n")
cat(paste(rep("=", 60), collapse=""), "\n\n")

# Check if interaction is significant
interaction_p <- anova_results$`Pr(>F)`[3]

if (!is.na(interaction_p) && interaction_p < 0.05) {{
  cat("⚠️ SIGNIFICANT INTERACTION DETECTED (p < 0.05)\n")
  cat("   Interpreting main effects may be misleading.\n")
  cat("   Examining simple effects instead...\n\n")

  # Simple effects: Compare factor1 levels within each level of factor2
  cat("📌 Simple Effects Analysis\n\n")

  emm_interaction <- emmeans(model, ~ {x_var_clean} | {group_var_clean})

  cat("🔸 Pairwise comparisons with Tukey adjustment:\n")
  print(pairs(emm_interaction, adjust = "tukey"))

  cat("\n🔸 Pairwise comparisons with Bonferroni adjustment:\n")
  print(pairs(emm_interaction, adjust = "bonferroni"))

  cat("\n🔸 Pairwise comparisons with Holm adjustment:\n")
  print(pairs(emm_interaction, adjust = "holm"))

  cat("\n🔸 Pairwise comparisons with FDR (Benjamini-Hochberg):\n")
  print(pairs(emm_interaction, adjust = "fdr"))

}} else {{
  cat("✓ No significant interaction - examining main effects\n\n")

  # Main effect of Factor 1
  factor1_p <- anova_results$`Pr(>F)`[1]
  if (!is.na(factor1_p) && factor1_p < 0.05) {{
    cat("📌 Post-hoc for {x_var_name} (significant main effect):\n\n")
    emm_factor1 <- emmeans(model, ~ {x_var_clean})

    cat("🔸 Tukey HSD (recommended for balanced designs):\n")
    print(pairs(emm_factor1, adjust = "tukey"))

    cat("\n🔸 Bonferroni (most conservative):\n")
    print(pairs(emm_factor1, adjust = "bonferroni"))

    cat("\n🔸 Holm (sequential Bonferroni, more power):\n")
    print(pairs(emm_factor1, adjust = "holm"))

    cat("\n🔸 FDR/Benjamini-Hochberg (controls false discovery rate):\n")
    print(pairs(emm_factor1, adjust = "fdr"))
  }} else {{
    cat("ℹ️ {x_var_name}: No significant main effect (p >= 0.05)\n")
  }}

  # Main effect of Factor 2
  factor2_p <- anova_results$`Pr(>F)`[2]
  if (!is.na(factor2_p) && factor2_p < 0.05) {{
    cat("\n📌 Post-hoc for {group_var_name} (significant main effect):\n\n")
    emm_factor2 <- emmeans(model, ~ {group_var_clean})

    cat("🔸 Tukey HSD:\n")
    print(pairs(emm_factor2, adjust = "tukey"))

    cat("\n🔸 Bonferroni:\n")
    print(pairs(emm_factor2, adjust = "bonferroni"))

    cat("\n🔸 Holm:\n")
    print(pairs(emm_factor2, adjust = "holm"))

    cat("\n🔸 FDR/Benjamini-Hochberg:\n")
    print(pairs(emm_factor2, adjust = "fdr"))
  }} else {{
    cat("\nℹ️ {group_var_name}: No significant main effect (p >= 0.05)\n")
  }}
}}

# ============================================================
# CORRECTION METHOD GUIDE
# ============================================================
cat("\n" , paste(rep("=", 60), collapse=""), "\n")
cat("💡 CHOOSING A CORRECTION METHOD\n")
cat(paste(rep("=", 60), collapse=""), "\n\n")
cat("• Tukey HSD: Best for balanced designs, all pairwise comparisons\n")
cat("• Bonferroni: Most conservative, controls familywise error strictly\n")
cat("• Holm: Less conservative than Bonferroni, more power, still controls FWER\n")
cat("• FDR (BH): Best for exploratory analysis, controls false discovery rate\n\n")
cat("Recommendation:\n")
cat("  - Confirmatory research → Bonferroni or Holm\n")
cat("  - Exploratory research → FDR\n")
cat("  - Balanced design with all comparisons → Tukey\n")

# Interaction Plot
cat("\n📉 Generating Interaction Plot...\n")
interaction.plot(x.factor = {x_var},
                 trace.factor = {group_var},
                 response = {y_var},
                 fun = mean,
                 type = "b",
                 legend = TRUE,
                 col = c("red", "blue", "green"),
                 pch = c(19, 17, 15),
                 fixed = TRUE,
                 xlab = "{x_var_name}",
                 trace.label = "{group_var_name}",
                 ylab = "Mean of {y_var_name}",
                 main = "Interaction Plot")

# Alternative Visualization (ggplot2)
ggplot({data}, aes(x = {x_var}, y = {y_var}, fill = {group_var})) +
  geom_boxplot(alpha = 0.7) +
  labs(title = "Two-Way ANOVA: Distribution by Groups",
       x = "{x_var_name}",
       y = "{y_var_name}",
       fill = "{group_var_name}") +
  theme_minimal()
