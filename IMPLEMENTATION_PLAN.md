# BioStation AI - Feature Implementation Plan

## Overview
This document outlines a **one-at-a-time** implementation strategy for adding missing features to BioStation AI. Each phase must be **fully completed, tested, and debugged** before moving to the next phase.

---

## Implementation Strategy

### Phase Completion Criteria
For each phase, we will:
1. ✅ **Plan** - Design the feature architecture
2. ✅ **Implement** - Write the code
3. ✅ **Test** - Test with real data
4. ✅ **Debug** - Fix any issues
5. ✅ **Document** - Update docs and comments
6. ✅ **Verify** - Final validation before moving on

**Rule:** No moving to the next phase until current phase is 100% complete and working.

---

## QUICK WINS (Phases 1-6)
*Low effort, high impact features*

### **Phase 1: Multiple Comparison Corrections**
**Duration:** 1-2 days
**Priority:** Critical Quick Win

**Scope:**
- Add Bonferroni correction method
- Add Holm-Bonferroni method
- Add False Discovery Rate (FDR/Benjamini-Hochberg)
- Add Dunn's test for Kruskal-Wallis
- Integrate into ANOVA and post-hoc test code

**Files to Modify:**
- `app/code_gen/generator.py` - Update ANOVA templates
- `app/advisor/test_knowledge.py` - Add correction method info
- `app/routes/chat.py` - Add intent handling for correction selection

**Implementation Steps:**
1. Update R code templates to include all correction methods
2. Add user option to select correction method
3. Modify LLM prompts to suggest appropriate corrections
4. Add educational content about when to use each method
5. Test with multi-group datasets

**Test Cases:**
- One-way ANOVA with Bonferroni
- One-way ANOVA with Holm
- One-way ANOVA with FDR
- Kruskal-Wallis with Dunn's test

---

### **Phase 2: Data Preview Feature**
**Duration:** 1 day
**Priority:** Quick Win

**Scope:**
- Show first 10 rows of uploaded dataset
- Display column names and data types
- Show basic stats (mean, median, min, max) for numeric columns
- Show unique values for categorical columns (if <10 unique values)

**Files to Modify:**
- `app/routes/file_handler.py` - Add preview generation on upload
- `app/chat_storage_manager/dataset_storage.py` - Store preview data
- Frontend (`app/templates/index.html`, `app/static/js/`) - Display preview UI

**Implementation Steps:**
1. Create `generate_preview()` function in file_handler
2. Return preview data in upload API response
3. Add frontend component to display preview table
4. Add "View Dataset" button in chat interface
5. Test with CSV and Excel files

**Test Cases:**
- Small dataset (10 rows)
- Large dataset (1000+ rows)
- Mixed data types (numeric + categorical)
- Missing values

---

### **Phase 3: Correlation Matrix Heatmap**
**Duration:** 1-2 days
**Priority:** Quick Win

**Scope:**
- Generate correlation matrix for all numeric columns
- Create heatmap visualization using ggplot2/corrplot
- Add statistical significance indicators
- Allow user to request correlation matrix via chat

**Files to Modify:**
- `app/code_gen/generator.py` - Add correlation matrix template
- `app/llm/keywords.py` - Add keywords for correlation matrix intent
- `app/routes/chat.py` - Add handler for correlation matrix requests

**Implementation Steps:**
1. Create R code template for correlation matrix
2. Add heatmap generation with corrplot package
3. Add intent detection for "show correlation matrix"
4. Generate both Pearson and Spearman matrices
5. Add p-value significance stars
6. Test with various dataset sizes

**Test Cases:**
- Dataset with 3 numeric columns
- Dataset with 10+ numeric columns
- Dataset with categorical columns (should be excluded)
- Handling missing values

---

### **Phase 4: Code Explanation using LLM**
**Duration:** 2 days
**Priority:** Quick Win

**Scope:**
- Add "Explain this code" button after code generation
- Use LLM to provide line-by-line explanation
- Highlight key statistical concepts in the code
- Explain assumptions being tested

**Files to Modify:**
- `app/routes/chat.py` - Add code explanation handler
- `app/llm/prompts.py` - Add code explanation prompts
- Frontend - Add "Explain Code" button

**Implementation Steps:**
1. Create LLM prompt for code explanation
2. Parse R code into logical sections
3. Generate explanations for each section
4. Format explanations with markdown
5. Add tooltips/expandable sections in UI
6. Test with various statistical tests

**Test Cases:**
- T-test code explanation
- ANOVA code explanation
- Regression code explanation
- Complex code with multiple steps

---

### **Phase 5: Built-in Dataset Library**
**Duration:** 1-2 days
**Priority:** Quick Win

**Scope:**
- Add R's built-in datasets (iris, mtcars, diamonds, etc.)
- Add biostatistics-specific datasets
- Provide dataset descriptions
- Suggest appropriate analyses for each dataset

**Files to Modify:**
- `app/routes/file_handler.py` - Add dataset loading endpoint
- `app/chat_storage_manager/dataset_storage.py` - Handle built-in datasets
- Create new module `app/datasets/builtin_datasets.py`

**Implementation Steps:**
1. Create catalog of built-in datasets
2. Add dataset metadata (description, variables, suggested analyses)
3. Create API endpoint to load built-in datasets
4. Add "Load Example Dataset" button in UI
5. Update chat to suggest datasets for practice
6. Test dataset loading and analysis

**Datasets to Include:**
- iris (classification, ANOVA)
- mtcars (regression, t-tests)
- diamonds (large dataset, correlation)
- ChickWeight (repeated measures)
- ToothGrowth (two-way ANOVA)
- PlantGrowth (one-way ANOVA)

---

### **Phase 6: Assumption Violation Warnings**
**Duration:** 2 days
**Priority:** Quick Win

**Scope:**
- Check test assumptions before running analysis
- Warn users when assumptions are violated
- Suggest alternative tests when assumptions fail
- Provide educational context about why assumptions matter

**Files to Modify:**
- `app/r_engine/validator.py` - Add assumption checking functions
- `app/code_gen/generator.py` - Add assumption tests to templates
- `app/routes/chat.py` - Add assumption checking before test execution

**Implementation Steps:**
1. Create assumption checking functions:
   - Normality (Shapiro-Wilk)
   - Homogeneity of variance (Levene's test)
   - Independence (Durbin-Watson)
   - Sample size requirements
2. Add warnings when assumptions violated
3. Suggest non-parametric alternatives
4. Add educational content about assumptions
5. Test with violating and non-violating data

**Test Cases:**
- Normal data → t-test passes
- Non-normal data → suggest Mann-Whitney
- Unequal variances → suggest Welch's t-test
- Small sample size → warn about power

---

## CRITICAL FEATURES (Phases 7-11)

### **Phase 7: Two-Way ANOVA**
**Duration:** 3-4 days
**Priority:** Critical

**Scope:**
- Implement two-way ANOVA (factorial design)
- Add interaction effect analysis
- Create interaction plots
- Add simple effects analysis
- Support both balanced and unbalanced designs

**Files to Modify:**
- `app/code_gen/generator.py` - Add two-way ANOVA template
- `app/advisor/decision_tree.py` - Update decision tree for factorial designs
- `app/llm/keywords.py` - Add two-way ANOVA keywords
- `app/routes/chat.py` - Add handler for two-way ANOVA

**Implementation Steps:**
1. Create R code template for two-way ANOVA
2. Add interaction term (factor1 * factor2)
3. Generate interaction plots
4. Add simple effects analysis
5. Add post-hoc tests for each factor
6. Test assumption checking (normality, homogeneity)
7. Add effect size (eta-squared, partial eta-squared)
8. Test with balanced and unbalanced designs

**Test Cases:**
- Balanced 2×2 design
- Balanced 3×3 design
- Unbalanced design
- Significant interaction
- No interaction

---

### **Phase 8: Repeated Measures ANOVA**
**Duration:** 4-5 days
**Priority:** Critical

**Scope:**
- Implement repeated measures ANOVA (within-subjects)
- Add sphericity testing (Mauchly's test)
- Apply Greenhouse-Geisser or Huynh-Feldt corrections
- Support mixed designs (between + within factors)
- Add profile plots

**Files to Modify:**
- `app/code_gen/generator.py` - Add repeated measures template
- `app/advisor/decision_tree.py` - Add repeated measures questions
- `app/r_engine/validator.py` - Add data format validation (wide/long)

**Implementation Steps:**
1. Create R code template using ezANOVA or afex package
2. Add sphericity testing
3. Apply corrections when sphericity violated
4. Add within-subject contrasts
5. Add profile plots over time
6. Support data reshaping (wide ↔ long format)
7. Test with different time points
8. Add mixed ANOVA (between + within)

**Test Cases:**
- Simple repeated measures (3 time points)
- Repeated measures with between-subject factor
- Violation of sphericity
- Missing data handling

---

### **Phase 9: Power Analysis & Sample Size Calculation**
**Duration:** 4 days
**Priority:** Critical

**Scope:**
- A priori power analysis (before study)
- Post-hoc power analysis (after study)
- Sample size calculation for common tests
- Effect size estimation
- Power curves visualization

**Files to Modify:**
- Create new module `app/power_analysis/calculator.py`
- `app/code_gen/generator.py` - Add power analysis templates
- `app/routes/chat.py` - Add power analysis handler
- `app/llm/keywords.py` - Add power analysis keywords

**Implementation Steps:**
1. Integrate pwr package in R
2. Create power analysis for:
   - t-tests (one-sample, two-sample, paired)
   - ANOVA (one-way, two-way)
   - Correlation
   - Regression
   - Chi-squared
3. Add sample size calculators
4. Generate power curves
5. Add effect size guidelines (small, medium, large)
6. Test various scenarios

**Test Cases:**
- Calculate sample size for medium effect
- Post-hoc power for existing study
- Power curve generation
- Multiple test types

---

### **Phase 10: Data Preprocessing & Cleaning Suite**
**Duration:** 5-6 days
**Priority:** Critical

**Scope:**
- Outlier detection (IQR, Z-score, Cook's distance)
- Data transformation (log, sqrt, Box-Cox)
- Missing data handling (imputation, deletion)
- Data reshaping (wide ↔ long)
- Variable recoding and binning

**Files to Modify:**
- Create new module `app/preprocessing/cleaner.py`
- Create new module `app/preprocessing/transformer.py`
- `app/routes/chat.py` - Add preprocessing handlers
- `app/r_engine/validator.py` - Add data quality checks

**Implementation Steps:**
1. **Outlier Detection:**
   - IQR method
   - Z-score method (±3 SD)
   - Cook's distance for regression
   - Visualization (boxplots)

2. **Data Transformation:**
   - Log transformation
   - Square root transformation
   - Box-Cox transformation
   - Standardization (z-scores)

3. **Missing Data:**
   - Identify missing patterns
   - Listwise deletion
   - Mean/median imputation
   - Multiple imputation (mice package)

4. **Data Reshaping:**
   - Wide to long format
   - Long to wide format
   - Pivot operations

5. **Variable Operations:**
   - Recoding (e.g., numeric to categorical)
   - Binning continuous variables
   - Creating dummy variables

6. Test each preprocessing operation

**Test Cases:**
- Dataset with outliers
- Non-normal data requiring transformation
- Missing data patterns
- Wide format dataset needing reshaping

---

### **Phase 11: Standalone Visualization Gallery**
**Duration:** 4-5 days
**Priority:** Critical

**Scope:**
- Create plots without running statistical tests
- Support multiple plot types
- Customizable aesthetics
- Export high-quality images

**Files to Modify:**
- Create new module `app/visualization/plotter.py`
- `app/routes/chat.py` - Add visualization handlers
- `app/code_gen/generator.py` - Add visualization templates

**Implementation Steps:**
1. **Basic Plots:**
   - Histogram with density curve
   - Box plots
   - Scatter plots
   - Bar charts
   - Line plots

2. **Advanced Plots:**
   - Violin plots
   - Raincloud plots
   - Faceted plots
   - Scatterplot matrix
   - Heatmaps

3. **Customization:**
   - Color schemes
   - Themes (minimal, classic, etc.)
   - Labels and titles
   - Axis limits

4. **Export:**
   - High DPI (300 DPI for publication)
   - Multiple formats (PNG, JPEG, PDF)
   - Custom dimensions

5. Test with various datasets

**Test Cases:**
- Single variable distribution
- Two variable relationship
- Multiple group comparison
- Time series plot

---

## IMPORTANT FEATURES (Phases 12-15)

### **Phase 12: Comprehensive Assumption Checking Suite**
**Duration:** 3-4 days
**Priority:** Important

**Scope:**
- Homogeneity of variance (Levene's, Bartlett's)
- Independence (Durbin-Watson)
- Linearity (residual plots)
- Multicollinearity (VIF)
- Outlier diagnostics (Cook's distance, leverage)

**Files to Modify:**
- Expand `app/r_engine/validator.py`
- `app/code_gen/generator.py` - Add diagnostic plots to templates

**Implementation Steps:**
1. Add variance homogeneity tests
2. Add independence checks
3. Create residual diagnostic plots
4. Add VIF calculation for regression
5. Add influence diagnostics
6. Generate comprehensive assumption report
7. Test with various datasets

---

### **Phase 13: Interactive Data Exploration**
**Duration:** 3 days
**Priority:** Important

**Scope:**
- Summary statistics table
- Frequency tables for categorical variables
- Cross-tabulation tables
- Variable distribution viewer

**Files to Modify:**
- Create new module `app/exploration/summarizer.py`
- `app/routes/chat.py` - Add exploration handlers
- Frontend - Add data exploration panel

**Implementation Steps:**
1. Create summary statistics function
2. Generate frequency tables
3. Add cross-tabulation
4. Create distribution visualizations
5. Add correlation matrix
6. Test with various data types

---

### **Phase 14: PCA & Multivariate Analysis**
**Duration:** 5-6 days
**Priority:** Important

**Scope:**
- Principal Component Analysis (PCA)
- Factor Analysis
- MANOVA
- Cluster Analysis (k-means, hierarchical)

**Files to Modify:**
- Create new module `app/multivariate/pca.py`
- `app/code_gen/generator.py` - Add multivariate templates
- `app/advisor/decision_tree.py` - Add multivariate decision path

**Implementation Steps:**
1. Implement PCA with scree plot
2. Add factor analysis
3. Implement MANOVA
4. Add k-means clustering
5. Add hierarchical clustering with dendrogram
6. Test with high-dimensional datasets

---

### **Phase 15: Advanced Regression Models**
**Duration:** 4-5 days
**Priority:** Important

**Scope:**
- Polynomial regression
- Ridge and Lasso regression
- Quantile regression
- Negative binomial regression
- Zero-inflated models

**Files to Modify:**
- `app/code_gen/generator.py` - Add regression templates
- `app/advisor/decision_tree.py` - Update regression decision path

**Implementation Steps:**
1. Add polynomial regression templates
2. Implement ridge/lasso using glmnet
3. Add quantile regression
4. Implement negative binomial
5. Add zero-inflated models
6. Test with appropriate datasets

---

## Progress Tracking

**Completion Status:**
- [x] Phase 1: Multiple Comparison Corrections ✅ (Completed: 2026-01-22)
- [x] Phase 2: Data Preview Feature ✅ (Completed: 2026-01-22)
- [x] Phase 3: Correlation Matrix Heatmap ✅ (Completed: 2026-01-23)
- [x] Phase 4: Code Explanation using LLM ✅ (Completed: 2026-01-23)
- [ ] Phase 5: Built-in Dataset Library
- [ ] Phase 6: Assumption Violation Warnings
- [ ] Phase 7: Two-Way ANOVA
- [ ] Phase 8: Repeated Measures ANOVA
- [ ] Phase 9: Power Analysis
- [ ] Phase 10: Data Preprocessing & Cleaning
- [ ] Phase 11: Visualization Gallery
- [ ] Phase 12: Assumption Checking Suite
- [ ] Phase 13: Interactive Data Exploration
- [ ] Phase 14: PCA & Multivariate
- [ ] Phase 15: Advanced Regression

---

## Estimated Timeline

**Quick Wins (Phases 1-6):** 8-12 days
**Critical Features (Phases 7-11):** 20-25 days
**Important Features (Phases 12-15):** 15-20 days

**Total Estimated Time:** 6-8 weeks (working sequentially)

---

## Next Steps

1. ✅ Review and approve this plan
2. ✅ Start with Phase 1: Multiple Comparison Corrections
3. ✅ Complete, test, and debug Phase 1
4. ✅ Move to Phase 2 only after Phase 1 is verified working
5. ✅ Continue one phase at a time

---

**Remember:** Quality over speed. Each feature must be fully functional and debugged before moving on.
