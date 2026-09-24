# Correlation Matrix with Heatmap
# Purpose: Generate correlation matrix for all numeric variables with visualization

# Load required packages
{package_helper}
ensure_package("ggplot2")
ensure_package("reshape2")
ensure_package("Hmisc")

library(ggplot2)
library(reshape2)
library(Hmisc)

# Load your data
{data_loading}

# Select only numeric columns
numeric_data <- {data}[, sapply({data}, is.numeric)]

if(ncol(numeric_data) < 2) {{
  stop("Need at least 2 numeric columns for correlation matrix")
}}

cat("📊 Correlation Matrix Analysis\n")
cat("================================\n\n")
cat("Numeric columns found:", ncol(numeric_data), "\n")
cat("Columns:", paste(names(numeric_data), collapse = ", "), "\n\n")

# Calculate correlation matrix with p-values using Hmisc
cor_result <- rcorr(as.matrix(numeric_data), type = "{correlation_method}")

# Extract correlation coefficients
cor_matrix <- cor_result$r

# Extract p-values
p_matrix <- cor_result$P

# Print correlation matrix
cat("\n📈 Correlation Coefficients ({correlation_method}):\n")
print(round(cor_matrix, 3))

# Print p-value matrix
cat("\n📉 P-values:\n")
print(round(p_matrix, 4))

# Create significance stars
get_stars <- function(p) {{
  if(is.na(p)) return("")
  if(p < 0.001) return("***")
  if(p < 0.01) return("**")
  if(p < 0.05) return("*")
  return("")
}}

# Interpretation guide
cat("\n📖 Interpretation Guide:\n")
cat("  Correlation strength: |r| < 0.3 weak, 0.3-0.7 moderate, > 0.7 strong\n")
cat("  Significance: * p<0.05, ** p<0.01, *** p<0.001\n")

# Melt correlation matrix for ggplot
melted_cor <- melt(cor_matrix)
names(melted_cor) <- c("Var1", "Var2", "Correlation")

# Create heatmap
heatmap_plot <- ggplot(melted_cor, aes(x = Var1, y = Var2, fill = Correlation)) +
  geom_tile(color = "white", linewidth = 0.5) +
  geom_text(aes(label = round(Correlation, 2)),
            color = ifelse(abs(melted_cor$Correlation) > 0.5, "white", "black"),
            size = 3.5) +
  scale_fill_gradient2(low = "#3B4CC0", mid = "white", high = "#B40426",
                       midpoint = 0, limits = c(-1, 1),
                       name = "Correlation") +
  labs(title = "Correlation Matrix Heatmap",
       subtitle = paste0("{correlation_method} correlation (n = ", nrow(numeric_data), ")"),
       x = "", y = "") +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1, vjust = 1),
    axis.text.y = element_text(hjust = 1),
    panel.grid = element_blank(),
    plot.title = element_text(hjust = 0.5, face = "bold"),
    plot.subtitle = element_text(hjust = 0.5)
  ) +
  coord_fixed()

print(heatmap_plot)

# Summary of significant correlations
cat("\n🔍 Significant Correlations (p < 0.05):\n")
sig_count <- 0
for(i in 1:(ncol(cor_matrix)-1)) {{
  for(j in (i+1):ncol(cor_matrix)) {{
    if(!is.na(p_matrix[i,j]) && p_matrix[i,j] < 0.05) {{
      sig_count <- sig_count + 1
      stars <- get_stars(p_matrix[i,j])
      cat(sprintf("  %s vs %s: r = %.3f %s (p = %.4f)\n",
          rownames(cor_matrix)[i], colnames(cor_matrix)[j],
          cor_matrix[i,j], stars, p_matrix[i,j]))
    }}
  }}
}}

if(sig_count == 0) {{
  cat("  No significant correlations found.\n")
}} else {{
  cat(sprintf("\n  Total: %d significant correlation(s) found.\n", sig_count))
}}
