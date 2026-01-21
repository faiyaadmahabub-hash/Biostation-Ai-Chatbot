# Install required R packages for BioStation AI

# List of packages
packages <- c(
  # Data manipulation
  "dplyr",
  "tidyr",
  "readr",
  "readxl", # Excel file support

  # Visualization
  "ggplot2",

  # Statistical tests
  "stats", # Built-in, but ensuring it's loaded
  "car", # Companion to Applied Regression (ANOVA, Levene's test)
  "lme4", # Linear mixed-effects models (GLMM)
  "lmerTest", # P-values for mixed models
  "mgcv", # GAM, GAMM
  "multcomp", # Multiple comparisons
  "dunn.test", # Dunn's test for Kruskal-Wallis post-hoc
  "nortest", # Normality tests (Anderson-Darling)
  "moments", # Skewness, kurtosis

  # Survival analysis
  "survival", # Cox regression, Kaplan-Meier
  "survminer", # Survival visualization

  # Additional utilities
  "broom" # Tidy statistical output
)

# Function to install if not already installed
install_if_missing <- function(pkg) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    cat(paste("Installing", pkg, "...\n"))
    install.packages(pkg, dependencies = TRUE, repos = "https://cran.r-project.org")
  } else {
    cat(paste(pkg, "already installed.\n"))
  }
}

# Install all packages
cat("BioStation AI - Installing R packages...\n\n")
sapply(packages, install_if_missing)

cat("\n✓ All R packages installed successfully!\n")
