"""
Explanation handlers for educational content and statistical concepts.

These handlers provide detailed explanations of statistical tests and
multiple comparison correction methods. Content is drawn from the
knowledge base when available, with LLM fallback for general questions.
"""

from typing import Any

from flask import current_app

from app.advisor import get_brief_explanation, get_full_explanation
from app.llm import PromptTemplates

from .base import TEST_MAPPING


def handle_explanation(message: str, client: Any) -> str:
    """
    Handle requests for statistical concept explanations.

    Checks for known test types first, then searches the guidebook
    knowledge base, and falls back to LLM generation for unknown topics.

    Args:
        message: User's question or topic request.
        client: LLM client for generating responses.

    Returns:
        Markdown-formatted explanation text.
    """
    message_lower = message.lower()
    test_id = _extract_test_id(message_lower)

    if test_id:
        return _generate_test_explanation(test_id, message_lower)

    # Search knowledge base for concept matches
    from app.guidebook import search_concepts

    concept_matches = search_concepts(message)
    if concept_matches:
        best_match = concept_matches[0]
        return f"""## {best_match['title']}

{best_match['content']}

---
*Want to learn about a different topic? Just ask!*"""

    # Fall back to LLM for general explanation
    return client.generate(
        prompt=message,
        system_prompt=PromptTemplates.GUIDEBOOK_SYNTHESIZER,
        temperature=current_app.config['LLM_TEMPERATURE']
    )


def _extract_test_id(message_lower: str) -> str:
    """Extract test ID from message using keyword matching."""
    for keyword, test_id in TEST_MAPPING.items():
        if keyword in message_lower:
            return test_id
    return ''


def _generate_test_explanation(test_id: str, message_lower: str) -> str:
    """
    Generate explanation for a known statistical test.

    Returns detailed explanation if user requests more detail,
    otherwise returns brief summary with prompts for next actions.
    """
    detail_keywords = ['detail', 'more', 'full', 'everything']
    wants_detail = any(word in message_lower for word in detail_keywords)

    if wants_detail:
        return get_full_explanation(test_id)

    brief = get_brief_explanation(test_id)
    return f"""{brief}

*Say "explain more" for detailed information, or "generate code" for R code.*"""


def handle_post_hoc(message: str, client: Any) -> str:
    """
    Handle requests about multiple comparison corrections and post-hoc tests.

    Provides detailed explanations of specific correction methods when
    mentioned, otherwise returns a general overview comparing all methods.

    Args:
        message: User's question about corrections.
        client: LLM client (unused, reserved for future extensions).

    Returns:
        Markdown-formatted explanation of correction method(s).
    """
    message_lower = message.lower()

    # Route to specific method explanations based on keywords
    if 'bonferroni' in message_lower:
        return _explain_bonferroni()

    if 'holm' in message_lower:
        return _explain_holm()

    if any(kw in message_lower for kw in ['fdr', 'benjamini', 'hochberg']):
        return _explain_fdr()

    if 'tukey' in message_lower:
        return _explain_tukey()

    # Default to general overview
    return _explain_corrections_overview()


def _explain_bonferroni() -> str:
    """Return Bonferroni correction explanation."""
    return """## Bonferroni Correction

**What it does:** Divides your significance level (alpha) by the number of tests.

**Formula:** Adjusted alpha = 0.05 / n (where n = number of comparisons)

**When to use:**
- Confirmatory research where false positives are costly
- Small number of planned comparisons
- Need to be very conservative

**Pros:** Simple, very conservative, controls familywise error rate (FWER)
**Cons:** Very strict - may miss real effects (low power)

**Example:** With 10 comparisons, only results with p < 0.005 are significant.

**R Code:**
```r
# Using pairwise.t.test
pairwise.t.test(data$outcome, data$group, p.adjust.method = "bonferroni")

# Using emmeans
library(emmeans)
emm <- emmeans(model, ~ group)
pairs(emm, adjust = "bonferroni")
```

*Want me to generate code with Bonferroni correction for your data?*"""


def _explain_holm() -> str:
    """Return Holm-Bonferroni correction explanation."""
    return """## Holm-Bonferroni Correction (Sequential Bonferroni)

**What it does:** Applies progressively less strict thresholds to ranked p-values.

**How it works:**
1. Rank p-values from smallest to largest
2. Compare smallest p to alpha/n, second smallest to alpha/(n-1), etc.
3. Stop when a p-value fails its threshold

**When to use:**
- Same situations as Bonferroni, but want more power
- Confirmatory research
- Controls FWER like Bonferroni but rejects more hypotheses

**Pros:** More powerful than Bonferroni, still controls FWER
**Cons:** Still conservative for exploratory work

**R Code:**
```r
# Using pairwise.t.test
pairwise.t.test(data$outcome, data$group, p.adjust.method = "holm")

# Using emmeans
library(emmeans)
emm <- emmeans(model, ~ group)
pairs(emm, adjust = "holm")
```

*Holm is generally preferred over Bonferroni - same error control, more power!*"""


def _explain_fdr() -> str:
    """Return FDR/Benjamini-Hochberg correction explanation."""
    return """## FDR (False Discovery Rate) / Benjamini-Hochberg

**What it does:** Controls the expected proportion of false discoveries among rejected hypotheses.

**Key concept:** Instead of controlling "any false positive", controls the *rate* of false positives.

**When to use:**
- Exploratory research (generating hypotheses)
- Many comparisons (genomics, proteomics, etc.)
- When some false positives are acceptable

**Pros:** Much more powerful than FWER methods, practical for many comparisons
**Cons:** Some false positives expected, not suitable for confirmatory research

**How it works:**
1. Rank p-values from smallest to largest
2. Compare each p to (rank/n) x alpha
3. Find largest p that passes, reject all smaller

**R Code:**
```r
# Using pairwise.t.test
pairwise.t.test(data$outcome, data$group, p.adjust.method = "fdr")

# Using p.adjust directly
adjusted_p <- p.adjust(p_values, method = "BH")

# Using emmeans
library(emmeans)
emm <- emmeans(model, ~ group)
pairs(emm, adjust = "fdr")
```

*FDR is ideal for exploratory analysis - find effects, then confirm with stricter tests!*"""


def _explain_tukey() -> str:
    """Return Tukey HSD explanation."""
    return """## Tukey's HSD (Honestly Significant Difference)

**What it does:** Compares all pairs of means while controlling familywise error rate.

**Best for:** All pairwise comparisons after ANOVA with balanced designs.

**When to use:**
- You want to compare all groups to each other
- Sample sizes are equal (or nearly equal)
- Post-ANOVA analysis

**Pros:** Designed specifically for all pairwise comparisons, widely used
**Cons:** Less powerful with unbalanced designs, only for pairwise

**R Code:**
```r
# After ANOVA
model <- aov(outcome ~ group, data = data)
TukeyHSD(model)

# Using emmeans
library(emmeans)
emm <- emmeans(model, ~ group)
pairs(emm, adjust = "tukey")
```

*Tukey is the default choice for post-hoc after one-way ANOVA!*"""


def _explain_corrections_overview() -> str:
    """Return general overview of all correction methods."""
    return """## Multiple Comparison Corrections Guide

When performing multiple statistical tests, the chance of at least one false positive increases dramatically. Corrections help control this error.

### Available Methods:

| Method | Controls | When to Use |
|--------|----------|-------------|
| **Bonferroni** | FWER (strictest) | Confirmatory research, few comparisons |
| **Holm** | FWER | Same as Bonferroni but more powerful |
| **Tukey HSD** | FWER | All pairwise comparisons after ANOVA |
| **FDR (BH)** | False Discovery Rate | Exploratory research, many comparisons |

### Quick Decision Guide:

**Ask yourself:**
1. Is this confirmatory or exploratory research?
   - Confirmatory -> **Holm** or **Bonferroni**
   - Exploratory -> **FDR**

2. How many comparisons?
   - Few (< 10) -> **Bonferroni/Holm** are fine
   - Many (10+) -> Consider **FDR**

3. After ANOVA with all pairwise comparisons?
   - Yes -> **Tukey HSD** is standard

### Quick R Code:
```r
# Pairwise comparisons with different corrections
pairwise.t.test(data$outcome, data$group, p.adjust.method = "bonferroni")
pairwise.t.test(data$outcome, data$group, p.adjust.method = "holm")
pairwise.t.test(data$outcome, data$group, p.adjust.method = "fdr")
```

---
*Ask me about a specific method (e.g., "explain Bonferroni") or say "generate ANOVA code" to get code with corrections!*"""
