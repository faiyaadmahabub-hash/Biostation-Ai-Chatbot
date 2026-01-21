"""
Guidebook - Educational content for statistical concepts
Provides detailed explanations, examples, and best practices.
"""

# Statistical Concepts Knowledge Base
# This serves as the RAG-ready knowledge base for the guidebook feature

STATISTICAL_CONCEPTS = {
    "normality": {
        "title": "Checking for Normality",
        "content": """
## What is Normality?

Normality refers to whether your data follows a **normal distribution** (bell curve). Many statistical tests assume your data is normally distributed.

## Why Does it Matter?

- **Parametric tests** (t-tests, ANOVA, Pearson correlation) assume normality
- If violated, results may be unreliable
- **Non-parametric alternatives** don't require normality

## How to Check Normality

### 1. Visual Methods
- **Histogram**: Should look bell-shaped
- **Q-Q Plot**: Points should follow the diagonal line

### 2. Statistical Tests
- **Shapiro-Wilk Test** (recommended for n < 50)
- **Kolmogorov-Smirnov Test** (for larger samples)
- **Anderson-Darling Test**

### R Code Example
```r
# Visual check
hist(data$variable, main="Histogram")
qqnorm(data$variable)
qqline(data$variable)

# Statistical test
shapiro.test(data$variable)
# p > 0.05 suggests normality
```

### What if Data Isn't Normal?
1. **Transform the data** (log, square root)
2. **Use non-parametric tests** (Mann-Whitney, Kruskal-Wallis)
3. **With large samples (n>30)**, Central Limit Theorem may apply
""",
        "keywords": ["normal", "normality", "shapiro", "distribution", "bell curve", "qq plot"]
    },
    
    "p_value": {
        "title": "Understanding P-Values",
        "content": """
## What is a P-Value?

The p-value is the probability of observing results at least as extreme as your data, **assuming the null hypothesis is true**.

## Common Misconceptions

❌ P-value is NOT the probability that the null hypothesis is true
❌ P-value is NOT the probability your results are due to chance
❌ A non-significant p-value does NOT prove the null hypothesis

## Interpreting P-Values

| P-value Range | Typical Interpretation |
|---------------|------------------------|
| p < 0.001     | Very strong evidence against H₀ |
| p < 0.01      | Strong evidence against H₀ |
| p < 0.05      | Moderate evidence against H₀ |
| p ≥ 0.05      | Insufficient evidence to reject H₀ |

## Best Practices

1. **Report exact p-values** (e.g., p = 0.032, not just p < 0.05)
2. **Consider effect size** alongside p-values
3. **Don't worship 0.05** - it's an arbitrary threshold
4. **Account for multiple comparisons** (Bonferroni, FDR)

## The "Significant" Trap

Statistical significance ≠ Practical significance!

A study with n = 10,000 might find p < 0.001 for a tiny, meaningless difference.
Always report **effect sizes** (Cohen's d, r², odds ratio).
""",
        "keywords": ["p-value", "significance", "hypothesis", "alpha", "0.05", "significant"]
    },
    
    "effect_size": {
        "title": "Effect Sizes Explained",
        "content": """
## What is Effect Size?

Effect size quantifies the **magnitude** of a difference or relationship, independent of sample size.

## Why Effect Size Matters

- P-values tell you IF there's an effect
- Effect sizes tell you HOW BIG the effect is
- Essential for practical interpretation

## Common Effect Size Measures

### For Comparing Means
| Measure | Formula | Interpretation |
|---------|---------|----------------|
| Cohen's d | (M₁ - M₂) / SD | 0.2 small, 0.5 medium, 0.8 large |
| Hedges' g | Similar to d, with correction | Better for small samples |

### For Correlations
| r Value | Interpretation |
|---------|----------------|
| 0.1 - 0.3 | Small |
| 0.3 - 0.5 | Medium |
| 0.5 - 1.0 | Large |

### For ANOVA
| Measure | Interpretation |
|---------|----------------|
| η² (Eta-squared) | Proportion of variance explained |
| ω² (Omega-squared) | Less biased than η² |

## R Code Examples
```r
# Cohen's d (using effsize package)
library(effsize)
cohen.d(group1, group2)

# For correlation, r IS the effect size
cor.test(x, y)$estimate

# Eta-squared from ANOVA
model <- aov(y ~ group, data)
summary(model)[[1]]["Sum Sq"] / sum(summary(model)[[1]]["Sum Sq"])
```
""",
        "keywords": ["effect size", "cohen", "eta squared", "magnitude", "practical significance"]
    },
    
    "parametric_vs_nonparametric": {
        "title": "Parametric vs Non-Parametric Tests",
        "content": """
## The Key Difference

**Parametric tests** assume your data follows a specific distribution (usually normal).
**Non-parametric tests** make no such assumptions - they work on ranked data.

## When to Use Each

### Use PARAMETRIC tests when:
✓ Data is approximately normally distributed
✓ Sample sizes are large (n > 30, Central Limit Theorem)
✓ Variances are roughly equal between groups
✓ You have continuous, interval/ratio data

### Use NON-PARAMETRIC tests when:
✓ Data is clearly non-normal
✓ Sample sizes are small
✓ You have ordinal data (rankings, Likert scales)
✓ Outliers are present and can't be removed

## Equivalent Tests

| Research Question | Parametric | Non-Parametric |
|-------------------|------------|----------------|
| Compare 2 independent groups | Independent t-test | Mann-Whitney U |
| Compare 2 paired groups | Paired t-test | Wilcoxon signed-rank |
| Compare 3+ independent groups | One-way ANOVA | Kruskal-Wallis |
| Correlation between 2 variables | Pearson's r | Spearman's rho |

## Trade-offs

**Parametric tests:**
- More statistical power when assumptions met
- More sensitive to detect real effects

**Non-parametric tests:**
- Safer when assumptions violated
- Less powerful (may miss real effects)
""",
        "keywords": ["parametric", "non-parametric", "nonparametric", "assumptions", "distribution-free"]
    },
    
    "multiple_comparisons": {
        "title": "The Multiple Comparisons Problem",
        "content": """
## The Problem

When you run multiple statistical tests, you increase the chance of false positives (Type I errors).

**Example:** Testing at α = 0.05 with 20 tests:
- Expected false positives: 20 × 0.05 = 1 false positive!

## Familywise Error Rate (FWER)

FWER = 1 - (1 - α)^n

With 20 tests at α = 0.05:
FWER = 1 - (0.95)^20 = 64% chance of at least one false positive!

## Solutions

### 1. Bonferroni Correction
Simplest but most conservative:
- New α = 0.05 / number of tests
- For 10 tests: α = 0.005

```r
# In R
p.adjust(p_values, method = "bonferroni")
```

### 2. Holm-Bonferroni (Recommended)
Less conservative, more powerful:
```r
p.adjust(p_values, method = "holm")
```

### 3. False Discovery Rate (FDR)
Controls proportion of false discoveries (Benjamini-Hochberg):
```r
p.adjust(p_values, method = "fdr")
```

### When to Correct
- Post-hoc tests after ANOVA (use Tukey's HSD)
- Multiple t-tests between groups
- Testing multiple outcomes
""",
        "keywords": ["multiple comparisons", "bonferroni", "correction", "fdr", "type i error", "false positive"]
    },
    
    "sample_size": {
        "title": "Sample Size and Power",
        "content": """
## Why Sample Size Matters

- Too small: May miss real effects (underpowered)
- Too large: Wastes resources, may find trivial effects
- Just right: High power to detect meaningful effects

## Statistical Power

**Power** = Probability of correctly rejecting H₀ when it's false
- Recommended: Power ≥ 0.80 (80%)
- Means: 80% chance of detecting a real effect

## Factors Affecting Required Sample Size

1. **Effect size**: Smaller effects need larger samples
2. **Significance level (α)**: Lower α needs larger samples
3. **Desired power**: Higher power needs larger samples
4. **Variability in data**: More variance needs larger samples

## Power Analysis in R
```r
library(pwr)

# For t-test
pwr.t.test(d = 0.5,  # medium effect size
           power = 0.8,
           sig.level = 0.05,
           type = "two.sample")

# For correlation
pwr.r.test(r = 0.3,
           power = 0.8,
           sig.level = 0.05)

# For ANOVA
pwr.anova.test(k = 3,  # 3 groups
               f = 0.25,  # medium effect
               power = 0.8)
```

## Rules of Thumb (Minimum)
- t-test: ~30 per group for medium effect
- Correlation: ~85 for medium effect
- ANOVA: ~25 per group for medium effect
""",
        "keywords": ["sample size", "power", "power analysis", "n", "participants", "subjects"]
    },
    
    "assumptions": {
        "title": "Checking Statistical Assumptions",
        "content": """
## Why Assumptions Matter

Statistical tests make assumptions about your data. Violating them can lead to:
- Incorrect p-values
- Biased estimates
- Invalid conclusions

## Common Assumptions & How to Check

### 1. Independence
- Observations don't influence each other
- **Check**: Study design (randomization, no repeated measures misuse)

### 2. Normality
- Data follows normal distribution
- **Check**: Shapiro-Wilk test, Q-Q plots
```r
shapiro.test(residuals)
qqnorm(residuals); qqline(residuals)
```

### 3. Homogeneity of Variance (Homoscedasticity)
- Equal variance across groups
- **Check**: Levene's test, residual plots
```r
library(car)
leveneTest(y ~ group, data)
```

### 4. Linearity
- Linear relationship between variables
- **Check**: Scatterplot, residual vs fitted plot
```r
plot(x, y)
plot(model$fitted, model$residuals)
```

### 5. No Multicollinearity (Regression)
- Predictors aren't highly correlated
- **Check**: VIF (Variance Inflation Factor)
```r
library(car)
vif(model)  # VIF > 5 is concerning
```

## What to Do When Assumptions Fail

1. **Transform data** (log, sqrt)
2. **Use robust methods** (robust SE, bootstrapping)
3. **Switch to non-parametric** tests
4. **Use different models** (GLM, mixed models)
""",
        "keywords": ["assumptions", "homogeneity", "variance", "independence", "linear", "check"]
    },
}


def search_concepts(query: str) -> list:
    """
    Search the knowledge base for relevant concepts.
    Returns a list of matching concepts.
    """
    from .dynamic_loader import load_knowledge_base
    
    # Load current knowledge (merged static + dynamic)
    current_concepts = load_knowledge_base()
    
    query_lower = query.lower()
    matches = []
    
    for concept_id, concept in current_concepts.items():
        score = 0
        
        # Check title
        if query_lower in concept["title"].lower():
            score += 10
        
        # Check keywords
        for keyword in concept["keywords"]:
            if keyword in query_lower:
                score += 5
        
        # Check content (basic)
        if query_lower in concept["content"].lower():
            score += 2
        
        if score > 0:
            matches.append({
                "id": concept_id,
                "title": concept["title"],
                "score": score,
                "content": concept["content"]
            })
    
    # Sort by score
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches


def get_concept(concept_id: str) -> dict:
    """Get a specific concept by ID"""
    from .dynamic_loader import load_knowledge_base
    return load_knowledge_base().get(concept_id)


def get_all_topics() -> list:
    """Get list of all available topics"""
    from .dynamic_loader import load_knowledge_base
    return [
        {"id": cid, "title": c["title"]}
        for cid, c in load_knowledge_base().items()
    ]
