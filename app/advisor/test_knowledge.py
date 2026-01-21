"""
Statistical Test Knowledge Base
Contains detailed information about each statistical test.
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class StatisticalTest:
    """Complete information about a statistical test"""
    id: str
    name: str
    also_known_as: List[str]
    category: str  # parametric, non-parametric, regression
    purpose: str
    use_when: List[str]
    assumptions: List[str]
    how_it_works: str
    interpretation: Dict[str, str]
    r_function: str
    r_packages: List[str]
    example_context: str
    common_mistakes: List[str]


# Complete knowledge base
STATISTICAL_TESTS: Dict[str, StatisticalTest] = {
    
    # ============ T-TESTS ============
    "one_sample_ttest": StatisticalTest(
        id="one_sample_ttest",
        name="One-Sample T-Test",
        also_known_as=["Single sample t-test"],
        category="parametric",
        purpose="Compare a sample mean to a known or hypothesized population mean",
        use_when=[
            "You have one group of continuous data",
            "You want to test if the mean differs from a specific value",
            "Data is approximately normally distributed"
        ],
        assumptions=[
            "Data is continuous",
            "Observations are independent",
            "Data is approximately normally distributed",
            "No significant outliers"
        ],
        how_it_works="Calculates how many standard errors the sample mean is from the hypothesized population mean. If this distance is large, we reject the null hypothesis.",
        interpretation={
            "p < 0.05": "Significant difference - sample mean differs from the hypothesized value",
            "p ≥ 0.05": "No significant difference - cannot conclude the mean differs"
        },
        r_function="t.test(x, mu = hypothesized_value)",
        r_packages=["stats"],
        example_context="Testing if the average enzyme activity in your samples differs from the literature value of 50 units.",
        common_mistakes=[
            "Using with non-normal data (use Wilcoxon signed-rank instead)",
            "Ignoring outliers that can skew results",
            "Confusing statistical significance with practical importance"
        ]
    ),
    
    "unpaired_ttest": StatisticalTest(
        id="unpaired_ttest",
        name="Independent Samples T-Test",
        also_known_as=["Two-sample t-test", "Unpaired t-test", "Student's t-test"],
        category="parametric",
        purpose="Compare means between two independent groups",
        use_when=[
            "Comparing two independent groups",
            "Outcome variable is continuous",
            "Data in both groups is approximately normal",
            "Groups are not matched or paired"
        ],
        assumptions=[
            "Independence of observations",
            "Normality in both groups",
            "Homogeneity of variances (or use Welch's t-test)",
            "Continuous dependent variable"
        ],
        how_it_works="Tests whether the difference between two group means is larger than expected by chance, accounting for variability within each group.",
        interpretation={
            "p < 0.05": "Significant difference between group means",
            "p ≥ 0.05": "No significant difference detected"
        },
        r_function="t.test(group1, group2) or t.test(value ~ group, data = df)",
        r_packages=["stats"],
        example_context="Comparing gene expression levels between treated and control cell cultures.",
        common_mistakes=[
            "Using when groups are paired/matched (use paired t-test)",
            "Ignoring unequal variances (use Welch's t-test: var.equal=FALSE)",
            "Using with small samples without checking normality"
        ]
    ),
    
    "paired_ttest": StatisticalTest(
        id="paired_ttest",
        name="Paired T-Test",
        also_known_as=["Dependent samples t-test", "Matched pairs t-test"],
        category="parametric",
        purpose="Compare means from the same subjects measured twice or matched pairs",
        use_when=[
            "Same subjects measured before and after treatment",
            "Matched pairs (e.g., twins)",
            "Repeated measurements on same experimental units",
            "Data is approximately normal"
        ],
        assumptions=[
            "Paired observations",
            "Differences between pairs are normally distributed",
            "Continuous data",
            "No significant outliers in the differences"
        ],
        how_it_works="Calculates the difference for each pair, then tests if the average difference is significantly different from zero.",
        interpretation={
            "p < 0.05": "Significant change between the two conditions",
            "p ≥ 0.05": "No significant change detected"
        },
        r_function="t.test(before, after, paired = TRUE)",
        r_packages=["stats"],
        example_context="Measuring blood pressure before and after drug administration in the same patients.",
        common_mistakes=[
            "Using unpaired t-test when data is paired (loses statistical power)",
            "Incorrect pairing order",
            "Not checking normality of differences"
        ]
    ),
    
    # ============ ANOVA ============
    "anova": StatisticalTest(
        id="anova",
        name="One-Way ANOVA",
        also_known_as=["Analysis of Variance", "F-test"],
        category="parametric",
        purpose="Compare means across three or more independent groups",
        use_when=[
            "Comparing 3 or more groups",
            "Continuous outcome variable",
            "Data is approximately normal in each group",
            "Groups are independent"
        ],
        assumptions=[
            "Independence of observations",
            "Normality within each group",
            "Homogeneity of variances (use Levene's test)",
            "Continuous dependent variable"
        ],
        how_it_works="Partitions total variance into between-group and within-group variance. If between-group variance is large relative to within-group variance, groups differ significantly.",
        interpretation={
            "p < 0.05": "At least one group mean differs significantly from the others",
            "p ≥ 0.05": "No significant differences among group means"
        },
        r_function="aov(value ~ group, data = df) or summary(aov(...))",
        r_packages=["stats", "car"],
        example_context="Comparing plant growth across 4 different fertilizer treatments.",
        common_mistakes=[
            "Not following up with post-hoc tests to identify which groups differ",
            "Using with unequal variances (use Welch's ANOVA)",
            "Running multiple t-tests instead (inflates Type I error)"
        ]
    ),
    
    # ============ NON-PARAMETRIC TESTS ============
    "mann_whitney": StatisticalTest(
        id="mann_whitney",
        name="Mann-Whitney U Test",
        also_known_as=["Wilcoxon rank-sum test", "Mann-Whitney-Wilcoxon test"],
        category="non-parametric",
        purpose="Compare two independent groups when data is not normally distributed",
        use_when=[
            "Comparing two independent groups",
            "Data is not normally distributed",
            "Ordinal or continuous data",
            "Sample sizes may be small"
        ],
        assumptions=[
            "Independence between groups",
            "Ordinal or continuous data",
            "Similar distribution shapes in both groups (for median comparison)"
        ],
        how_it_works="Ranks all observations from both groups together and tests whether one group tends to have higher ranks than the other.",
        interpretation={
            "p < 0.05": "Significant difference between groups",
            "p ≥ 0.05": "No significant difference detected"
        },
        r_function="wilcox.test(group1, group2) or wilcox.test(value ~ group, data = df)",
        r_packages=["stats"],
        example_context="Comparing patient satisfaction scores (ordinal 1-5) between two hospitals.",
        common_mistakes=[
            "Using when data is normal (t-test has more power)",
            "Interpreting as a test of medians when distributions differ",
            "Ignoring ties in the data"
        ]
    ),
    
    "wilcoxon_signed_rank": StatisticalTest(
        id="wilcoxon_signed_rank",
        name="Wilcoxon Signed-Rank Test",
        also_known_as=["Wilcoxon matched pairs test"],
        category="non-parametric",
        purpose="Compare paired samples when data is not normally distributed",
        use_when=[
            "Paired or matched observations",
            "Data is not normally distributed",
            "Before/after measurements on same subjects",
            "Ordinal or continuous data"
        ],
        assumptions=[
            "Paired observations",
            "Differences are symmetric around the median",
            "Ordinal or continuous data"
        ],
        how_it_works="Ranks the absolute differences between pairs, then compares the sum of positive and negative ranks.",
        interpretation={
            "p < 0.05": "Significant change between conditions",
            "p ≥ 0.05": "No significant change detected"
        },
        r_function="wilcox.test(before, after, paired = TRUE)",
        r_packages=["stats"],
        example_context="Comparing pain levels before and after treatment when pain scores are non-normal.",
        common_mistakes=[
            "Using when observations are independent (use Mann-Whitney)",
            "Ignoring zero differences",
            "Not checking symmetry assumption"
        ]
    ),
    
    "kruskal_wallis": StatisticalTest(
        id="kruskal_wallis",
        name="Kruskal-Wallis Test",
        also_known_as=["Kruskal-Wallis H test", "One-way ANOVA on ranks"],
        category="non-parametric",
        purpose="Compare three or more independent groups when data is not normally distributed",
        use_when=[
            "Comparing 3 or more groups",
            "Data is not normally distributed",
            "Ordinal or continuous data",
            "Groups are independent"
        ],
        assumptions=[
            "Independence between groups",
            "Ordinal or continuous data",
            "Similar distribution shapes across groups"
        ],
        how_it_works="Ranks all observations together and tests if the mean ranks differ significantly among groups.",
        interpretation={
            "p < 0.05": "At least one group differs significantly from the others",
            "p ≥ 0.05": "No significant differences among groups"
        },
        r_function="kruskal.test(value ~ group, data = df)",
        r_packages=["stats"],
        example_context="Comparing bacteria colony counts across 4 different growth media.",
        common_mistakes=[
            "Not following up with post-hoc tests (Dunn's test)",
            "Using when ANOVA assumptions are met (less power)",
            "Ignoring tied observations"
        ]
    ),
    
    # ============ CORRELATION ============
    "pearson_correlation": StatisticalTest(
        id="pearson_correlation",
        name="Pearson Correlation",
        also_known_as=["Pearson's r", "Pearson product-moment correlation"],
        category="parametric",
        purpose="Measure the strength and direction of linear relationship between two continuous variables",
        use_when=[
            "Both variables are continuous",
            "Relationship is linear",
            "Data is normally distributed",
            "Looking for linear association"
        ],
        assumptions=[
            "Both variables are continuous",
            "Linear relationship",
            "Bivariate normality",
            "No significant outliers",
            "Homoscedasticity"
        ],
        how_it_works="Measures how closely data points cluster around a straight line. Ranges from -1 (perfect negative) to +1 (perfect positive).",
        interpretation={
            "r close to 1": "Strong positive linear relationship",
            "r close to -1": "Strong negative linear relationship",
            "r close to 0": "Little or no linear relationship",
            "p < 0.05": "Correlation is statistically significant"
        },
        r_function="cor.test(x, y, method = 'pearson')",
        r_packages=["stats"],
        example_context="Examining the relationship between body mass and metabolic rate in animals.",
        common_mistakes=[
            "Assuming correlation implies causation",
            "Using with non-linear relationships",
            "Ignoring outliers that can drastically affect r"
        ]
    ),
    
    "spearman_correlation": StatisticalTest(
        id="spearman_correlation",
        name="Spearman Correlation",
        also_known_as=["Spearman's rho", "Spearman rank correlation"],
        category="non-parametric",
        purpose="Measure monotonic relationship between two variables (ordinal or non-normal continuous)",
        use_when=[
            "Data is ordinal or not normally distributed",
            "Relationship may be monotonic but not linear",
            "Outliers are present",
            "Assessing rank-order relationship"
        ],
        assumptions=[
            "Monotonic relationship (both increase or both decrease)",
            "Ordinal or continuous data",
            "Observations are independent"
        ],
        how_it_works="Converts values to ranks, then calculates Pearson correlation on the ranks. Less sensitive to outliers.",
        interpretation={
            "rho close to 1": "Strong positive monotonic relationship",
            "rho close to -1": "Strong negative monotonic relationship",
            "rho close to 0": "Little or no monotonic relationship",
            "p < 0.05": "Correlation is statistically significant"
        },
        r_function="cor.test(x, y, method = 'spearman')",
        r_packages=["stats"],
        example_context="Examining relationship between education level (ordinal) and income.",
        common_mistakes=[
            "Using when Pearson is appropriate (may lose precision)",
            "Expecting it to detect non-monotonic relationships",
            "Ignoring tied values"
        ]
    ),
    
    # ============ CHI-SQUARED & FISHER ============
    "chi_squared": StatisticalTest(
        id="chi_squared",
        name="Chi-Squared Test",
        also_known_as=["Chi-square test of independence", "Pearson's chi-squared"],
        category="non-parametric",
        purpose="Test association between two categorical variables",
        use_when=[
            "Both variables are categorical",
            "Expected frequencies ≥ 5 in each cell",
            "Testing independence/association",
            "Adequate sample size"
        ],
        assumptions=[
            "Random sampling",
            "Independent observations",
            "Expected frequency ≥ 5 in each cell",
            "Categorical data"
        ],
        how_it_works="Compares observed frequencies to expected frequencies under independence assumption. Large discrepancies suggest association.",
        interpretation={
            "p < 0.05": "Significant association between variables",
            "p ≥ 0.05": "No significant association detected"
        },
        r_function="chisq.test(table(var1, var2))",
        r_packages=["stats"],
        example_context="Testing if treatment response (yes/no) is associated with patient sex (male/female).",
        common_mistakes=[
            "Using with small expected frequencies (use Fisher's exact)",
            "Confusing with chi-squared goodness of fit",
            "Ignoring effect size (Cramer's V)"
        ]
    ),
    
    "fisher_exact": StatisticalTest(
        id="fisher_exact",
        name="Fisher's Exact Test",
        also_known_as=["Fisher-Irwin test"],
        category="non-parametric",
        purpose="Test association between categorical variables with small sample sizes",
        use_when=[
            "Small sample sizes",
            "Expected cell counts < 5",
            "2x2 contingency table (can extend to larger)",
            "Testing independence"
        ],
        assumptions=[
            "Fixed row and column totals",
            "Independent observations",
            "Categorical data"
        ],
        how_it_works="Calculates the exact probability of observing the current table (or more extreme) under the null hypothesis of independence.",
        interpretation={
            "p < 0.05": "Significant association between variables",
            "p ≥ 0.05": "No significant association detected"
        },
        r_function="fisher.test(table(var1, var2))",
        r_packages=["stats"],
        example_context="Testing if a rare mutation is associated with disease status in a small patient cohort.",
        common_mistakes=[
            "Using chi-squared when sample is too small",
            "Ignoring one-sided vs two-sided test choice",
            "Misinterpreting odds ratio"
        ]
    ),
    
    # ============ REGRESSION MODELS ============
    "linear_regression": StatisticalTest(
        id="linear_regression",
        name="Linear Regression",
        also_known_as=["OLS regression", "Multiple regression"],
        category="regression",
        purpose="Model the relationship between a continuous outcome and one or more predictors",
        use_when=[
            "Predicting a continuous outcome",
            "Multiple predictor variables",
            "Linear relationships",
            "Assessing effect of predictors"
        ],
        assumptions=[
            "Linearity",
            "Independence of residuals",
            "Homoscedasticity (constant variance)",
            "Normality of residuals",
            "No multicollinearity"
        ],
        how_it_works="Finds the best-fitting line (or hyperplane) that minimizes the sum of squared differences between observed and predicted values.",
        interpretation={
            "R²": "Proportion of variance explained by the model",
            "p-value (coefficient)": "Significance of each predictor",
            "Coefficient": "Change in outcome per unit change in predictor"
        },
        r_function="lm(outcome ~ predictor1 + predictor2, data = df)",
        r_packages=["stats"],
        example_context="Predicting plant biomass from soil nutrient levels and sunlight hours.",
        common_mistakes=[
            "Ignoring residual diagnostics",
            "Including highly correlated predictors",
            "Extrapolating beyond data range"
        ]
    ),
    
    "glm": StatisticalTest(
        id="glm",
        name="Generalized Linear Model",
        also_known_as=["GLM", "Logistic regression (for binary)", "Poisson regression (for counts)"],
        category="regression",
        purpose="Model relationships when the outcome is not normally distributed",
        use_when=[
            "Binary outcome (logistic regression)",
            "Count data (Poisson regression)",
            "Non-normal error distributions",
            "Need for link function"
        ],
        assumptions=[
            "Correct specification of link function",
            "Independence of observations",
            "Correct distribution family",
            "No overdispersion (or account for it)"
        ],
        how_it_works="Extends linear regression by using a link function to relate the linear predictor to the mean of the outcome distribution.",
        interpretation={
            "Coefficients": "Effect on the link scale (e.g., log-odds for logistic)",
            "Odds ratio (logistic)": "Multiplicative effect on odds",
            "p-value": "Significance of each predictor"
        },
        r_function="glm(outcome ~ predictors, family = binomial/poisson, data = df)",
        r_packages=["stats"],
        example_context="Predicting disease presence (0/1) from biomarkers using logistic regression.",
        common_mistakes=[
            "Wrong family/link specification",
            "Ignoring overdispersion in count data",
            "Confusing coefficients with probabilities"
        ]
    ),
    
    "glmm": StatisticalTest(
        id="glmm",
        name="Generalized Linear Mixed Model",
        also_known_as=["GLMM", "Mixed effects model", "Multilevel model"],
        category="regression",
        purpose="Model non-normal data with random effects for non-independent observations",
        use_when=[
            "Repeated measures",
            "Nested/hierarchical data",
            "Non-independent observations",
            "Non-normal outcome"
        ],
        assumptions=[
            "Correct random effects structure",
            "Correct distribution family",
            "Independence within clusters after accounting for random effects"
        ],
        how_it_works="Combines GLM with random effects to account for correlation within groups/clusters/subjects.",
        interpretation={
            "Fixed effects": "Population-average effects",
            "Random effects": "Subject/group-specific deviations",
            "Variance components": "Variability at different levels"
        },
        r_function="glmer(outcome ~ fixed + (1|random), family = ..., data = df)",
        r_packages=["lme4", "lmerTest"],
        example_context="Modeling patient recovery (binary) over time with random intercepts for each patient.",
        common_mistakes=[
            "Overly complex random effects structure",
            "Convergence issues",
            "Misspecifying crossed vs nested effects"
        ]
    ),
    
    "gam": StatisticalTest(
        id="gam",
        name="Generalized Additive Model",
        also_known_as=["GAM", "Additive model"],
        category="regression",
        purpose="Model non-linear relationships using smooth functions",
        use_when=[
            "Non-linear relationships",
            "Unknown functional form",
            "Need for flexibility",
            "Continuous predictors with curved effects"
        ],
        assumptions=[
            "Additive effects",
            "No overfitting (smoothness penalty)",
            "Independence of observations"
        ],
        how_it_works="Replaces linear coefficients with smooth functions (splines) that are estimated from the data.",
        interpretation={
            "Smooth terms": "Visualize the non-linear relationship",
            "edf (effective degrees of freedom)": "Complexity of the smooth (1 = linear)",
            "p-value": "Significance of smooth terms"
        },
        r_function="gam(outcome ~ s(predictor), data = df)",
        r_packages=["mgcv"],
        example_context="Modeling species abundance along an environmental gradient with non-linear response.",
        common_mistakes=[
            "Overfitting with too many basis functions",
            "Ignoring concurvity (GAM equivalent of multicollinearity)",
            "Not checking residuals"
        ]
    ),
    
    # ============ SURVIVAL ANALYSIS ============
    "kaplan_meier": StatisticalTest(
        id="kaplan_meier",
        name="Kaplan-Meier Survival Analysis",
        also_known_as=["Product-limit estimator", "KM curve"],
        category="survival",
        purpose="Estimate survival probabilities over time and compare survival curves between groups",
        use_when=[
            "You have time-to-event data (e.g., time to death, disease recurrence)",
            "Some observations are censored (event hasn't occurred yet)",
            "Comparing survival between two or more groups",
            "Estimating median survival time"
        ],
        assumptions=[
            "Censoring is non-informative (censored subjects have same prognosis as non-censored)",
            "Survival probabilities are constant over time within risk sets",
            "Event times are exactly known"
        ],
        how_it_works="Estimates the survivor function by calculating the cumulative probability of surviving beyond each event time, accounting for censored observations. The log-rank test compares survival curves between groups.",
        interpretation={
            "Survival curve": "Shows probability of surviving beyond each time point",
            "Median survival": "Time at which 50% of subjects have experienced the event",
            "Log-rank p < 0.05": "Significant difference in survival between groups",
            "95% CI": "Confidence interval for survival probability at each time"
        },
        r_function="survfit(Surv(time, event) ~ group); survdiff(Surv(time, event) ~ group)",
        r_packages=["survival", "survminer"],
        example_context="Comparing survival times of cancer patients receiving different treatments, accounting for patients lost to follow-up.",
        common_mistakes=[
            "Ignoring censoring and analyzing only complete cases",
            "Confusing censoring indicator (0 vs 1)",
            "Not checking if censoring is informative",
            "Comparing groups with very different follow-up times"
        ]
    ),
    
    "cox_regression": StatisticalTest(
        id="cox_regression",
        name="Cox Proportional Hazards Regression",
        also_known_as=["Cox regression", "Cox model", "Proportional hazards model"],
        category="survival",
        purpose="Model the relationship between survival time and one or more predictor variables",
        use_when=[
            "Analyzing time-to-event data with covariates",
            "Adjusting for confounding variables in survival analysis",
            "Estimating hazard ratios",
            "Identifying risk factors for an event"
        ],
        assumptions=[
            "Proportional hazards (hazard ratio is constant over time)",
            "Non-informative censoring",
            "Linear relationship between log hazard and predictors",
            "No influential outliers"
        ],
        how_it_works="Models the hazard function as a product of a baseline hazard and an exponential function of covariates. Hazard ratios express the multiplicative effect of predictors on the hazard.",
        interpretation={
            "HR = 1": "No effect of predictor on hazard",
            "HR > 1": "Increased hazard (worse survival)",
            "HR < 1": "Decreased hazard (better survival)",
            "p < 0.05": "Predictor significantly affects survival"
        },
        r_function="coxph(Surv(time, event) ~ predictors)",
        r_packages=["survival", "survminer"],
        example_context="Modeling time to tumor recurrence as a function of age, treatment type, and tumor stage.",
        common_mistakes=[
            "Not testing proportional hazards assumption",
            "Including too many predictors relative to number of events",
            "Confusing hazard ratios with odds ratios",
            "Ignoring interaction effects"
        ]
    ),
    
    # ============ ASSUMPTION TESTING ============
    "normality_test": StatisticalTest(
        id="normality_test",
        name="Normality Testing",
        also_known_as=["Shapiro-Wilk test", "Anderson-Darling test", "Q-Q plot"],
        category="assumption",
        purpose="Test whether data follows a normal (Gaussian) distribution",
        use_when=[
            "Before using parametric tests (t-test, ANOVA, regression)",
            "Checking assumptions of statistical analyses",
            "Deciding between parametric vs non-parametric tests",
            "Validating regression model residuals"
        ],
        assumptions=[
            "Data is continuous",
            "Observations are independent",
            "Sufficient sample size (Shapiro-Wilk: 3-5000 observations)"
        ],
        how_it_works="Shapiro-Wilk tests if data deviates from normality using W statistic. Anderson-Darling gives more weight to tails. Q-Q plots visually compare data quantiles to theoretical normal quantiles.",
        interpretation={
            "p > 0.05": "Data is likely normally distributed (fail to reject H0)",
            "p < 0.05": "Data significantly deviates from normality",
            "Q-Q plot linear": "Data follows normal distribution",
            "Q-Q plot curved": "Data deviates from normality"
        },
        r_function="shapiro.test(x); ad.test(x); qqnorm(x); qqline(x)",
        r_packages=["stats", "nortest"],
        example_context="Testing if residuals from a linear regression are normally distributed before interpreting results.",
        common_mistakes=[
            "Relying solely on p-value with large samples (overly sensitive)",
            "Ignoring visual inspection (Q-Q plot)",
            "Testing normality of outcome instead of residuals in regression",
            "Using histogram alone without formal tests"
        ]
    ),
    
    # ============ DESCRIPTIVE STATISTICS ============
    "descriptive": StatisticalTest(
        id="descriptive",
        name="Descriptive Statistics",
        also_known_as=["Summary statistics", "Basic statistics"],
        category="descriptive",
        purpose="Calculate mean, median, variance, standard deviation, and other summary measures for your data",
        use_when=[
            "You want to understand the distribution of your data",
            "Before running more complex statistical tests",
            "Exploring your dataset for the first time",
            "Reporting central tendency and variability"
        ],
        assumptions=[
            "Data should be numeric for most statistics",
            "Outliers can heavily influence mean and variance"
        ],
        how_it_works="Calculates summary measures like mean (average), median (middle value), variance (spread), and standard deviation to describe your data distribution.",
        interpretation={
            "Mean": "The average value of your data",
            "Median": "The middle value when data is sorted",
            "SD": "How spread out the data is from the mean",
            "Variance": "The squared spread from the mean"
        },
        r_function="summary(data); mean(x); sd(x); var(x)",
        r_packages=["stats", "dplyr"],
        example_context="Getting summary statistics for plant heights before comparing treatment groups.",
        common_mistakes=[
            "Reporting only mean without variability measures",
            "Ignoring outliers that skew the mean",
            "Using mean for ordinal data (use median instead)"
        ]
    ),
}


def get_test_info(test_id: str) -> StatisticalTest:
    """Get information about a specific test"""
    return STATISTICAL_TESTS.get(test_id)


def get_brief_explanation(test_id: str) -> str:
    """Get a brief 2-3 sentence explanation of a test"""
    test = get_test_info(test_id)
    if not test:
        return "Test not found."
    
    return f"**{test.name}**: {test.purpose}. Use this when: {test.use_when[0].lower()}."


def get_full_explanation(test_id: str) -> str:
    """Get a detailed explanation of a test"""
    test = get_test_info(test_id)
    if not test:
        return "Test not found."
    
    explanation = f"""## {test.name}
{'*Also known as: ' + ', '.join(test.also_known_as) + '*' if test.also_known_as else ''}

**Purpose:** {test.purpose}

**When to use:**
{chr(10).join('• ' + item for item in test.use_when)}

**How it works:**
{test.how_it_works}

**Assumptions:**
{chr(10).join('• ' + item for item in test.assumptions)}

**Interpretation:**
{chr(10).join('• **' + k + '**: ' + v for k, v in test.interpretation.items())}

**R Code:**
```r
{test.r_function}
```

**Example context:**
{test.example_context}

**Common mistakes to avoid:**
{chr(10).join('⚠️ ' + item for item in test.common_mistakes)}
"""
    return explanation
