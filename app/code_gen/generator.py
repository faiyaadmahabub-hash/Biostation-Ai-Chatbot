"""
R Code Generator - Creates ready-to-run R code for statistical analyses
"""

from typing import Dict, Optional
from app.advisor.test_knowledge import get_test_info


class RCodeGenerator:
    """Generates R code for statistical tests"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load R code templates for each test"""
        
        # Helper R function to check and install packages
        pkg_helper = '''
# Function to ensure packages are installed
ensure_package <- function(pkg) {{
  if (!require(pkg, character.only = TRUE)) {{
    cat(paste("Installing missing package:", pkg, "\\n"))
    install.packages(pkg, repos = "https://cloud.r-project.org")
    if (!require(pkg, character.only = TRUE)) {{
      stop(paste("Failed to install package:", pkg))
    }}
  }}
}}
'''
        
        return {
            # ============ T-TESTS ============
            "one_sample_ttest": pkg_helper + '''# One-Sample T-Test
# Purpose: Compare sample mean to a known value

# Load required packages
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Check normality (optional but recommended)
shapiro_test <- shapiro.test({y_var})
cat("Shapiro-Wilk normality test p-value:", shapiro_test$p.value, "\\n")
if (shapiro_test$p.value < 0.05) {{
  cat("Warning: Data may not be normally distributed. Consider Wilcoxon test.\\n")
}}

# Perform one-sample t-test
# H0: Mean = {mu} (hypothesized value)
result <- t.test({y_var}, mu = {mu})

# Print results
print(result)

# Calculate effect size (Cohen's d)
cohens_d <- (mean({y_var}) - {mu}) / sd({y_var})
cat("\\nEffect size (Cohen's d):", round(cohens_d, 3), "\\n")

# Visualization
ggplot(data.frame(x = {y_var}), aes(x = x)) +
  geom_histogram(aes(y = after_stat(density)), bins = 20, fill = "steelblue", alpha = 0.7) +
  geom_density(color = "darkblue", linewidth = 1) +
  geom_vline(xintercept = {mu}, color = "red", linetype = "dashed", linewidth = 1) +
  geom_vline(xintercept = mean({y_var}), color = "green", linewidth = 1) +
  labs(title = "Distribution of {y_var_name}",
       subtitle = paste("Sample mean (green) vs. Hypothesized (red):", {mu}),
       x = "{y_var_name}", y = "Density") +
  theme_minimal()
''',
            
            "unpaired_ttest": pkg_helper + '''# Independent Samples T-Test (Unpaired)
# Purpose: Compare means between two independent groups

# Load required packages
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Check normality in each group
cat("Checking normality:\\n")
for (grp in unique({group_var})) {{
  subset_data <- {y_var}[{group_var} == grp]
  if (length(subset_data) >= 3) {{
    shap <- shapiro.test(subset_data)
    cat("  Group", grp, "- Shapiro p-value:", round(shap$p.value, 4), "\\n")
  }}
}}

# Check homogeneity of variances
var_test <- var.test({y_var} ~ {group_var}, data = {data})
cat("\\nLevene's test for equal variances p-value:", round(var_test$p.value, 4), "\\n")

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
cat("\\nEffect size (Cohen's d):", round(cohens_d, 3), "\\n")

# Visualization
ggplot({data}, aes(x = {group_var}, y = {y_var}, fill = {group_var})) +
  geom_boxplot(alpha = 0.7) +
  geom_jitter(width = 0.2, alpha = 0.5) +
  labs(title = "Comparison of {y_var_name} by {group_var_name}",
       x = "{group_var_name}", y = "{y_var_name}") +
  theme_minimal() +
  theme(legend.position = "none")
''',
            
            "paired_ttest": pkg_helper + '''# Paired T-Test
# Purpose: Compare means from paired/matched observations

# Load required packages
ensure_package("ggplot2")
ensure_package("tidyr")
library(ggplot2)
library(tidyr)

# Load your data
{data_loading}

# Calculate differences
differences <- {after_var} - {before_var}

# Check normality of differences
shapiro_test <- shapiro.test(differences)
cat("Shapiro-Wilk test on differences p-value:", shapiro_test$p.value, "\\n")
if (shapiro_test$p.value < 0.05) {{
  cat("Warning: Differences may not be normal. Consider Wilcoxon signed-rank test.\\n")
}}

# Perform paired t-test
result <- t.test({before_var}, {after_var}, paired = TRUE)

# Print results
print(result)

# Effect size (Cohen's d for paired data)
cohens_d <- mean(differences) / sd(differences)
cat("\\nEffect size (Cohen's d):", round(cohens_d, 3), "\\n")

# Visualization - Before/After plot
plot_data <- data.frame(
  id = 1:length({before_var}),
  Before = {before_var},
  After = {after_var}
) |> pivot_longer(cols = c(Before, After), names_to = "Time", values_to = "Value")

ggplot(plot_data, aes(x = Time, y = Value, group = id)) +
  geom_line(alpha = 0.3) +
  geom_point(aes(color = Time), size = 3) +
  stat_summary(aes(group = 1), fun = mean, geom = "line", color = "red", linewidth = 1.5) +
  stat_summary(aes(group = 1), fun = mean, geom = "point", color = "red", size = 4) +
  labs(title = "Before vs After Comparison",
       subtitle = "Individual pairs (gray) and mean (red)") +
  theme_minimal()
''',
            
            # ============ ANOVA ============
            "anova": pkg_helper + '''# One-Way ANOVA
# Purpose: Compare means across 3+ groups

# Load required packages
ensure_package("ggplot2")
ensure_package("car")
ensure_package("multcomp")
library(ggplot2)
library(car)        # For Levene's test
library(multcomp)   # For Tukey HSD

# Load your data
{data_loading}

# Check assumptions
cat("🔍 Assumption Checks\\n\\n")

# 1. Normality (Shapiro-Wilk per group)
cat("Normality by group:\\n")
for (grp in unique({group_var})) {{
  subset_data <- {y_var}[{group_var} == grp]
  if (length(subset_data) >= 3 & length(subset_data) <= 5000) {{
    shap <- shapiro.test(subset_data)
    cat("  ", grp, "- p =", round(shap$p.value, 4), "\\n")
  }}
}}

# 2. Homogeneity of variances
levene <- leveneTest({y_var} ~ as.factor({group_var}), data = {data})
cat("\\nLevene's test p-value:", round(levene$`Pr(>F)`[1], 4), "\\n")

# Perform ANOVA
cat("\\n📊 ANOVA Results\\n")
model <- aov({y_var} ~ {group_var}, data = {data})
print(summary(model))

# Effect size (Eta-squared)
ss_between <- summary(model)[[1]]["Sum Sq"][1,1]
ss_total <- sum(summary(model)[[1]]["Sum Sq"])
eta_sq <- ss_between / ss_total
cat("\\nEffect size (Eta-squared):", round(eta_sq, 3), "\\n")

# Post-hoc: Tukey's HSD (if ANOVA is significant)
if (summary(model)[[1]]["Pr(>F)"][1,1] < 0.05) {{
  cat("\\n🔍 Post-hoc: Tukey's HSD\\n")
  tukey <- TukeyHSD(model)
  print(tukey)
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
''',
            
            # ============ NON-PARAMETRIC ============
            "mann_whitney": pkg_helper + '''# Mann-Whitney U Test (Wilcoxon Rank-Sum)
# Purpose: Compare two independent groups (non-parametric)

# Load required packages
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Perform Mann-Whitney U test
result <- wilcox.test({y_var} ~ {group_var}, data = {data})

# Print results
cat("📊 Mann-Whitney U Test\\n")
print(result)

# Effect size (r = Z / sqrt(N))
# Approximate calculation
n <- length({y_var})
z <- qnorm(result$p.value / 2)
effect_r <- abs(z) / sqrt(n)
cat("\\nEffect size (r):", round(effect_r, 3))
cat("\\nInterpretation: small=0.1, medium=0.3, large=0.5\\n")

# Summary statistics by group
cat("\\n📈 Group Medians\\n")
print(aggregate({y_var} ~ {group_var}, data = {data}, FUN = median))

# Visualization
ggplot({data}, aes(x = {group_var}, y = {y_var}, fill = {group_var})) +
  geom_violin(alpha = 0.5) +
  geom_boxplot(width = 0.2, alpha = 0.8) +
  labs(title = "Mann-Whitney U Test: Comparison",
       x = "{group_var_name}", y = "{y_var_name}") +
  theme_minimal() +
  theme(legend.position = "none")
''',
            
            "wilcoxon_signed_rank": pkg_helper + '''# Wilcoxon Signed-Rank Test
# Purpose: Compare paired samples (non-parametric)

# Load required packages
ensure_package("ggplot2")
ensure_package("tidyr")
library(ggplot2)
library(tidyr)

# Load your data
{data_loading}

# Perform Wilcoxon signed-rank test
result <- wilcox.test({before_var}, {after_var}, paired = TRUE)

# Print results
cat("📊 Wilcoxon Signed-Rank Test\\n")
print(result)

# Median of differences
differences <- {after_var} - {before_var}
cat("\\nMedian difference:", median(differences), "\\n")

# Visualization
plot_data <- data.frame(
  Before = {before_var},
  After = {after_var}
) |> pivot_longer(cols = everything(), names_to = "Time", values_to = "Value")

ggplot(plot_data, aes(x = Time, y = Value, fill = Time)) +
  geom_boxplot(alpha = 0.7) +
  labs(title = "Wilcoxon Signed-Rank: Before vs After") +
  theme_minimal()
''',
            
            "kruskal_wallis": pkg_helper + '''# Kruskal-Wallis Test
# Purpose: Compare 3+ groups (non-parametric)

# Load required packages
ensure_package("ggplot2")
ensure_package("dunn.test")
library(ggplot2)
library(dunn.test)  # For post-hoc

# Load your data
{data_loading}

# Perform Kruskal-Wallis test
result <- kruskal.test({y_var} ~ {group_var}, data = {data})

# Print results
cat("📊 Kruskal-Wallis Test\\n")
print(result)

# Post-hoc: Dunn's test (if significant)
if (result$p.value < 0.05) {{
  cat("\\n🔍 Post-hoc: Dunn's Test\\n")
  dunn.test({y_var}, {group_var}, method = "bonferroni")
}}

# Summary statistics by group
cat("\\n📈 Group Medians\\n")
print(aggregate({y_var} ~ {group_var}, data = {data}, FUN = median))

# Visualization
ggplot({data}, aes(x = {group_var}, y = {y_var}, fill = {group_var})) +
  geom_violin(alpha = 0.5) +
  geom_boxplot(width = 0.2, alpha = 0.8) +
  labs(title = "Kruskal-Wallis: Group Comparison") +
  theme_minimal() +
  theme(legend.position = "none")
''',
            
            # ============ CORRELATION ============
            "pearson_correlation": pkg_helper + '''# Pearson Correlation
# Purpose: Measure linear relationship between two continuous variables

# Load required packages
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Perform Pearson correlation test
result <- cor.test({x_var}, {y_var}, method = "pearson")

# Print results
cat("📊 Pearson Correlation\\n")
print(result)

cat("\\nInterpretation of r:")
cat("\\n  |r| < 0.3 = weak")
cat("\\n  0.3 ≤ |r| < 0.7 = moderate")
cat("\\n  |r| ≥ 0.7 = strong\\n")

# Visualization
ggplot({data}, aes(x = {x_var}, y = {y_var})) +
  geom_point(alpha = 0.6) +
  geom_smooth(method = "lm", color = "blue", se = TRUE) +
  labs(title = paste("Pearson r =", round(result$estimate, 3)),
       subtitle = paste("p-value =", format(result$p.value, digits = 3)),
       x = "{x_var_name}", y = "{y_var_name}") +
  theme_minimal()
''',
            
            "spearman_correlation": pkg_helper + '''# Spearman Correlation
# Purpose: Measure monotonic relationship (non-parametric)

# Load required packages
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Perform Spearman correlation test
result <- cor.test({x_var}, {y_var}, method = "spearman")

# Print results
cat("📊 Spearman Correlation\\n")
print(result)

# Visualization
ggplot({data}, aes(x = {x_var}, y = {y_var})) +
  geom_point(alpha = 0.6) +
  geom_smooth(method = "loess", color = "purple", se = TRUE) +
  labs(title = paste("Spearman rho =", round(result$estimate, 3)),
       subtitle = paste("p-value =", format(result$p.value, digits = 3)),
       x = "{x_var_name}", y = "{y_var_name}") +
  theme_minimal()
''',
            
            # ============ CHI-SQUARED & FISHER ============
            "chi_squared": pkg_helper + '''# Chi-Squared Test of Independence
# Purpose: Test association between two categorical variables

# Load required packages
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Create contingency table
cont_table <- table({var1}, {var2})
cat("📋 Contingency Table\\n")
print(cont_table)

# Check expected frequencies
expected <- chisq.test(cont_table)$expected
cat("\\n🎲 Expected Frequencies\\n")
print(round(expected, 1))
if (any(expected < 5)) {{
  cat("\\nWarning: Some expected frequencies < 5. Consider Fisher's exact test.\\n")
}}

# Perform chi-squared test
result <- chisq.test(cont_table)

cat("\\n📊 Chi-Squared Test\\n")
print(result)

# Effect size (Cramer's V)
n <- sum(cont_table)
min_dim <- min(nrow(cont_table), ncol(cont_table)) - 1
cramers_v <- sqrt(result$statistic / (n * min_dim))
cat("\\nEffect size (Cramer's V):", round(cramers_v, 3))
cat("\\nInterpretation: small=0.1, medium=0.3, large=0.5\\n")

# Visualization
mosaicplot(cont_table, main = "Mosaic Plot", color = TRUE)
''',
            
            "fisher_exact": pkg_helper + '''# Fisher's Exact Test
# Purpose: Test association with small sample sizes

# Load your data
{data_loading}

# Create contingency table
cont_table <- table({var1}, {var2})
cat("📋 Contingency Table\\n")
print(cont_table)

# Perform Fisher's exact test
result <- fisher.test(cont_table)

cat("\\n📊 Fisher's Exact Test\\n")
print(result)

# Odds ratio interpretation (for 2x2 tables)
if (nrow(cont_table) == 2 & ncol(cont_table) == 2) {{
  cat("\\nOdds Ratio:", round(result$estimate, 3))
  cat("\\n95% CI:", round(result$conf.int[1], 3), "-", round(result$conf.int[2], 3), "\\n")
}}
''',
            
            # ============ REGRESSION ============
            "linear_regression": pkg_helper + '''# Linear Regression
# Purpose: Model relationship between outcome and predictors

# Load required packages
ensure_package("ggplot2")
ensure_package("car")
library(ggplot2)
library(car)  # For diagnostic plots

# Load your data
{data_loading}

# Fit linear model
model <- lm({y_var} ~ {predictors}, data = {data})

# Model summary
cat("=== Linear Regression Results ===\\n")
print(summary(model))

# Confidence intervals for coefficients
cat("\\n=== 95% Confidence Intervals ===\\n")
print(confint(model))

# Model diagnostics
cat("\\n=== Diagnostic Checks ===\\n")
cat("Checking: Linearity, Normality of residuals, Homoscedasticity\\n")

# Diagnostic plots
par(mfrow = c(2, 2))
plot(model)
par(mfrow = c(1, 1))

# VIF for multicollinearity (if multiple predictors)
if (length(attr(terms(model), "term.labels")) > 1) {{
  cat("\\n=== Variance Inflation Factors ===\\n")
  print(vif(model))
  cat("VIF > 5 suggests multicollinearity concern\\n")
}}
''',
            
            "glm": pkg_helper + '''# Generalized Linear Model (Logistic/Poisson)
# Purpose: Model non-normal outcomes

# Load required packages
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

# Fit GLM
# family = binomial for binary outcome (logistic regression)
# family = poisson for count data
model <- glm({y_var} ~ {predictors}, family = {family}, data = {data})

# Model summary
cat("=== GLM Results ===\\n")
print(summary(model))

# For logistic regression: Odds ratios
if ("{family}" == "binomial") {{
  cat("\\n=== Odds Ratios ===\\n")
  print(exp(coef(model)))
  cat("\\n95% CI for Odds Ratios:\\n")
  print(exp(confint(model)))
}}

# Model fit
cat("\\nAIC:", AIC(model))
cat("\\nNull deviance:", model$null.deviance)
cat("\\nResidual deviance:", model$deviance, "\\n")
''',
            
            "descriptive": pkg_helper + '''# Descriptive Statistics
# Purpose: Calculate mean, variance, and summary stats

# Load required packages
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
''',
            
            # ============ GLMM ============
            "glmm": pkg_helper + '''# Generalized Linear Mixed Model (GLMM)
# Purpose: Model non-normal data with random effects for non-independent observations

# Load required packages
ensure_package("lme4")
ensure_package("lmerTest")
library(lme4)
library(lmerTest)

# Load your data
{data_loading}

# Fit GLMM
# For binary outcome: family = binomial
# For count data: family = poisson
# (1|{random_var}) = random intercept for {random_var}
model <- glmer({y_var} ~ {fixed_effects} + (1|{random_var}), 
                 family = {family}, 
                 data = {data})

# Model summary
cat("=== GLMM Results ===\\n")
print(summary(model))

# Random effects variance
cat("\\n=== Random Effects ===\\n")
print(VarCorr(model))

# Fixed effects confidence intervals
cat("\\n=== 95% CI for Fixed Effects ===\\n")
print(confint(model, parm = "beta_"))

# For logistic GLMM: Odds ratios
if ("{family}" == "binomial") {
  cat("\\n=== Odds Ratios ===\\n")
  fixed_effects <- fixef(model)
  print(exp(fixed_effects))
}

# Model diagnostics
cat("\\n=== Model Diagnostics ===\\n")
cat("AIC:", AIC(model), "\\n")
cat("BIC:", BIC(model), "\\n")

# Residual plots
plot(model)
''',
            
            # ============ GAM ============
            "gam": pkg_helper + '''# Generalized Additive Model (GAM)
# Purpose: Model non-linear relationships using smooth functions

# Load required packages
ensure_package("mgcv")
library(mgcv)

# Load your data
{data_loading}

# Fit GAM with smooth terms
# s() creates smooth functions
# k = basis dimension (lower = smoother, higher = more flexible)
model <- gam({y_var} ~ s({smooth_var}, k = 10), 
              data = {data})

# Model summary
cat("=== GAM Results ===\\n")
print(summary(model))

cat("\\n📈 Interpreting edf (effective degrees of freedom):\\n")
cat("  edf ≈ 1: Linear relationship\\n")
cat("  edf > 1: Non-linear relationship\\n")
cat("  Higher edf = more complex curve\\n\\n")

# Model fit statistics
cat("R-squared (adjusted):", round(summary(model)$r.sq, 3), "\\n")
cat("Deviance explained:", round(summary(model)$dev.expl * 100, 1), "%\\n")
cat("AIC:", round(AIC(model), 2), "\\n\\n")

# Check for concurvity (GAM's version of multicollinearity)
cat("=== Concurvity Check ===\\n")
print(concurvity(model, full = TRUE))
cat("Values close to 1 suggest high concurvity\\n\\n")

# Visualize smooth terms
cat("=== Smooth Term Visualization ===\\n")
plot(model, residuals = TRUE, pch = 1, cex = 0.5)

# Diagnostic plots
par(mfrow = c(2, 2))
gam.check(model)
par(mfrow = c(1, 1))
''',
            
            # ============ SURVIVAL ANALYSIS ============
            "kaplan_meier": pkg_helper + '''# Kaplan-Meier Survival Analysis
# Purpose: Estimate survival probabilities over time

# Load required packages
ensure_package("survival")
ensure_package("survminer")
library(survival)
library(survminer)

# Load your data
{data_loading}

# Create survival object
# time_var = time to event or censoring
# event_var = 1 if event occurred, 0 if censored
surv_obj <- Surv(time = {time_var}, event = {event_var})

# Fit Kaplan-Meier curves
km_fit <- survfit(surv_obj ~ {group_var}, data = {data})

# Print summary
cat("=== Kaplan-Meier Survival Analysis ===\\n")
print(km_fit)

# Median survival times
cat("\\n=== Median Survival Times ===\\n")
print(summary(km_fit)$table)

# Log-rank test (compare survival curves between groups)
cat("\\n=== Log-Rank Test ===\\n")
logrank_test <- survdiff(surv_obj ~ {group_var}, data = {data})
print(logrank_test)

if (logrank_test$pvalue < 0.05) {
  cat("\\n✓ Significant difference in survival between groups (p < 0.05)\\n")
} else {
  cat("\\n✗ No significant difference in survival between groups (p ≥ 0.05)\\n")
}

# Survival curve plot
ggsurvplot(
  km_fit,
  data = {data},
  pval = TRUE,
  conf.int = TRUE,
  risk.table = TRUE,
  risk.table.col = "strata",
  linetype = "strata",
  surv.median.line = "hv",
  ggtheme = theme_minimal(),
  title = "Kaplan-Meier Survival Curves",
  xlab = "Time",
  ylab = "Survival Probability"
)
''',
            
            "cox_regression": pkg_helper + '''# Cox Proportional Hazards Regression
# Purpose: Model time-to-event data with covariates

# Load required packages
ensure_package("survival")
ensure_package("survminer")
library(survival)
library(survminer)

# Load your data
{data_loading}

# Create survival object
surv_obj <- Surv(time = {time_var}, event = {event_var})

# Fit Cox regression model
cox_model <- coxph(surv_obj ~ {predictors}, data = {data})

# Model summary
cat("=== Cox Proportional Hazards Regression ===\\n")
print(summary(cox_model))

# Hazard ratios with confidence intervals
cat("\\n=== Hazard Ratios ===\\n")
hr <- exp(coef(cox_model))
hr_ci <- exp(confint(cox_model))
hr_table <- cbind(HR = hr, hr_ci)
print(round(hr_table, 3))

cat("\\n📊 Interpreting Hazard Ratios:\\n")
cat("  HR = 1: No effect\\n")
cat("  HR > 1: Increased hazard (worse survival)\\n")
cat("  HR < 1: Decreased hazard (better survival)\\n\\n")

# Test proportional hazards assumption
cat("=== Proportional Hazards Assumption Test ===\\n")
ph_test <- cox.zph(cox_model)
print(ph_test)

if (any(ph_test$table[,"p"] < 0.05)) {
  cat("\\n⚠️ Warning: Proportional hazards assumption may be violated (p < 0.05)\\n")
  cat("   Consider stratification or time-varying coefficients\\n")
} else {
  cat("\\n✓ Proportional hazards assumption satisfied (p ≥ 0.05)\\n")
}

# Plot Schoenfeld residuals
plot(ph_test)

# Forest plot of hazard ratios
ggforest(cox_model, data = {data})
''',
            
            # ============ NORMALITY TESTING ============
            "normality_test": pkg_helper + '''# Normality Testing
# Purpose: Test if data follows a normal distribution

# Load required packages
ensure_package("ggplot2")
library(ggplot2)

# Load your data
{data_loading}

cat("=== Normality Tests for {y_var_name} ===\\n\\n")

# 1. Shapiro-Wilk test (best for n < 5000)
if (length({y_var}) >= 3 & length({y_var}) <= 5000) {
  shapiro_result <- shapiro.test({y_var})
  cat("📊 Shapiro-Wilk Test\\n")
  cat("   W =", round(shapiro_result$statistic, 4), "\\n")
  cat("   p-value =", format.pval(shapiro_result$p.value, digits = 4), "\\n")
  
  if (shapiro_result$p.value < 0.05) {
    cat("   ✗ Data is NOT normally distributed (p < 0.05)\\n\\n")
  } else {
    cat("   ✓ Data appears normally distributed (p ≥ 0.05)\\n\\n")
  }
} else if (length({y_var}) > 5000) {
  cat("⚠️ Sample size > 5000. Shapiro-Wilk may be too sensitive.\\n")
  cat("   Consider visual inspection (Q-Q plot) instead.\\n\\n")
}

# 2. Anderson-Darling test (alternative)
ensure_package("nortest")
library(nortest)
ad_result <- ad.test({y_var})
cat("📊 Anderson-Darling Test\\n")
cat("   A =", round(ad_result$statistic, 4), "\\n")
cat("   p-value =", format.pval(ad_result$p.value, digits = 4), "\\n")
if (ad_result$p.value < 0.05) {
  cat("   ✗ Data is NOT normally distributed (p < 0.05)\\n\\n")
} else {
  cat("   ✓ Data appears normally distributed (p ≥ 0.05)\\n\\n")
}

# 3. Descriptive statistics
cat("📈 Descriptive Statistics\\n")
cat("   Mean:", round(mean({y_var}, na.rm = TRUE), 3), "\\n")
cat("   Median:", round(median({y_var}, na.rm = TRUE), 3), "\\n")
cat("   SD:", round(sd({y_var}, na.rm = TRUE), 3), "\\n")
ensure_package("moments") # Ensure moments package is loaded for skewness/kurtosis
library(moments)
cat("   Skewness:", round(moments::skewness({y_var}, na.rm = TRUE), 3), "\\n")
cat("   Kurtosis:", round(moments::kurtosis({y_var}, na.rm = TRUE), 3), "\\n\\n")

# 4. Visualization: Q-Q Plot
cat("📊 Generating Q-Q Plot...\\n")
qqnorm({y_var}, main = "Q-Q Plot: {y_var_name}")
qqline({y_var}, col = "red", lwd = 2)

# 5. Visualization: Histogram with Normal Curve
x <- {y_var}
hist_data <- data.frame(x = x)

ggplot(hist_data, aes(x = x)) +
  geom_histogram(aes(y = after_stat(density)), 
                 bins = 30, fill = "steelblue", alpha = 0.7, color = "white") +
  geom_density(color = "darkblue", linewidth = 1) +
  stat_function(
    fun = dnorm, 
    args = list(mean = mean(x, na.rm = TRUE), sd = sd(x, na.rm = TRUE)),
    color = "red", linewidth = 1, linetype = "dashed"
  ) +
  labs(
    title = "Histogram with Normal Overlay",
    subtitle = "Blue = Actual density, Red dashed = Normal distribution",
    x = "{y_var_name}",
    y = "Density"
  ) +
  theme_minimal()

cat("\\n💡 Interpretation Guide:\\n")
cat("   • If p > 0.05: Data is likely normal\\n")
cat("   • If p < 0.05: Data is likely NOT normal\\n")
cat("   • Q-Q plot points should fall on the red line if normal\\n")
cat("   • Histogram should match the red dashed normal curve\\n")
'''
        }
    
    def generate_code(
        self,
        test_id: str,
        data_source: str = "your_data.csv",
        variables: Dict[str, str] = None,
        parameters: Dict[str, str] = None,
        column_context: list = None
    ) -> str:
        """
        Generate R code for a specific test.
        
        Args:
            test_id: ID of the statistical test
            data_source: Path to data file or data frame name
            variables: Dict mapping variable roles to column names
            parameters: Additional parameters (e.g., mu for one-sample t-test)
            column_context: List of actual column names from the dataset (optional)
        
        Returns:
            Complete R code as string
        """
        if test_id not in self.templates:
            return f"# Error: No template available for {test_id}"
        
        template = self.templates[test_id]
        
        # Default variable mappings
        vars = variables or {}
        params = parameters or {}
        
        # Intelligent column guessing if context is provided but vars are empty
        if column_context and not vars:
            # Simple heuristic: take first column as outcome (y), second as predictor (x/group)
            if len(column_context) > 0:
                vars["y"] = f"data${column_context[-1]}"  # Often last col is outcome
                vars["y_name"] = column_context[-1]
                vars["y_clean"] = column_context[-1]
            
            if len(column_context) > 1:
                vars["x"] = f"data${column_context[0]}"
                vars["x_name"] = column_context[0]
                vars["group"] = f"data${column_context[0]}"
                vars["group_name"] = column_context[0]
        
        # Create data loading code
        if data_source.endswith('.csv'):
            data_loading = f'data <- read.csv("{data_source}")'
        elif data_source.endswith(('.xlsx', '.xls')):
            data_loading = f'library(readxl)\ndata <- read_excel("{data_source}")'
        else:
            data_loading = f'# data <- {data_source}  # Your data frame'
        
        # Helper to clean variable names (remove data$ prefix for some uses)
        def clean_var(v):
            return v.replace("data$", "").replace('"', '')

        # Replace placeholders
        code = template.format(
            data_loading=data_loading,
            data="data",
            y_var=vars.get("y", "data$outcome"),
            y_var_name=vars.get("y_name", "Outcome Variable"),
            y_var_clean=clean_var(vars.get("y", "outcome")),
            x_var=vars.get("x", "data$predictor"),
            x_var_name=vars.get("x_name", "Predictor Variable"),
            group_var=vars.get("group", "data$group"),
            group_var_name=vars.get("group_name", "Group"),
            before_var=vars.get("before", "data$before"),
            after_var=vars.get("after", "data$after"),
            var1=vars.get("var1", "data$variable1"),
            var2=vars.get("var2", "data$variable2"),
            predictors=vars.get("predictors", "predictor1 + predictor2"),
            # GLMM parameters
            random_var=vars.get("random", "data$subject_id"),
            fixed_effects=vars.get("fixed_effects", "predictor1 + predictor2"),
            # GAM parameters
            smooth_var=vars.get("smooth", "data$predictor"),
            # Survival analysis parameters
            time_var=vars.get("time", "data$time"),
            event_var=vars.get("event", "data$status"),
            # General parameters
            mu=params.get("mu", "0"),
            family=params.get("family", "binomial"),
            **params
        )
        
        return code


# Singleton instance
code_generator = RCodeGenerator()
