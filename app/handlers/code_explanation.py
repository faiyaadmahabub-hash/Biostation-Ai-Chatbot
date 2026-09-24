"""
Code Explanation Handler - Provides LLM-powered explanations for R code.

This module enables users to get detailed, educational explanations of
R statistical code, breaking down each section and explaining the
statistical concepts involved.
"""

import re
import logging
from typing import Any, Dict, Generator, Optional

from app.llm import PromptTemplates

logger = logging.getLogger(__name__)


def handle_code_explanation(
    code: str,
    client: Any,
    test_type: Optional[str] = None,
    stream: bool = True
) -> Generator[str, None, None]:
    """
    Generate an LLM-powered explanation of R code.

    Args:
        code: The R code to explain
        client: LLM client for generating explanations
        test_type: Optional type of statistical test for context
        stream: Whether to stream the response

    Yields:
        Chunks of the explanation text
    """
    if not code or not code.strip():
        yield "**No code provided to explain.**\n\nPlease provide R code to get an explanation."
        return

    # Clean up the code (remove markdown code block markers if present)
    cleaned_code = _clean_code(code)

    # Detect test type if not provided
    if not test_type:
        test_type = _detect_test_type(cleaned_code)

    # Generate the prompt
    prompt = PromptTemplates.get_code_explanation_prompt(cleaned_code, test_type)

    # Get system prompt
    system_prompt = PromptTemplates.CODE_EXPLAINER

    try:
        if stream:
            # Stream the response
            response_stream = client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for more focused explanations
                stream=True
            )

            for chunk in response_stream:
                yield chunk
        else:
            # Non-streaming response
            response = client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                stream=False
            )
            yield response

    except Exception as e:
        logger.error(f"Error generating code explanation: {e}")
        yield f"**Error generating explanation:** {str(e)}\n\nPlease try again."


def _clean_code(code: str) -> str:
    """
    Clean up code by removing markdown code block markers.

    Args:
        code: Raw code that may contain markdown markers

    Returns:
        Cleaned code without markdown markers
    """
    # Remove ```r or ``` markers
    code = re.sub(r'^```r?\s*\n?', '', code, flags=re.MULTILINE)
    code = re.sub(r'\n?```\s*$', '', code, flags=re.MULTILINE)
    return code.strip()


def _detect_test_type(code: str) -> Optional[str]:
    """
    Detect the type of statistical test from the R code.

    Args:
        code: R code to analyze

    Returns:
        Detected test type or None if not identifiable
    """
    code_lower = code.lower()

    # T-tests
    if 't.test(' in code_lower:
        if 'paired' in code_lower and 'true' in code_lower:
            return 'Paired T-Test'
        return 'T-Test'

    # ANOVA
    if 'aov(' in code_lower or 'anova(' in code_lower:
        if '*' in code and 'aov(' in code_lower:
            return 'Two-Way ANOVA'
        return 'One-Way ANOVA'

    # Non-parametric tests
    if 'wilcox.test(' in code_lower:
        if 'paired' in code_lower:
            return 'Wilcoxon Signed-Rank Test'
        return 'Mann-Whitney U Test'

    if 'kruskal.test(' in code_lower:
        return 'Kruskal-Wallis Test'

    # Correlation
    if 'cor.test(' in code_lower or 'rcorr(' in code_lower:
        if 'spearman' in code_lower:
            return 'Spearman Correlation'
        if 'kendall' in code_lower:
            return 'Kendall Correlation'
        return 'Pearson Correlation'

    # Regression (check glm before lm to avoid false matches)
    if 'glm(' in code_lower:
        if 'binomial' in code_lower:
            return 'Logistic Regression'
        if 'poisson' in code_lower:
            return 'Poisson Regression'
        return 'Generalized Linear Model'

    if 'lm(' in code_lower:
        return 'Linear Regression'

    # Chi-squared
    if 'chisq.test(' in code_lower:
        return 'Chi-Squared Test'

    if 'fisher.test(' in code_lower:
        return "Fisher's Exact Test"

    # Survival analysis
    if 'survfit(' in code_lower or 'kaplan' in code_lower:
        return 'Kaplan-Meier Survival Analysis'

    if 'coxph(' in code_lower:
        return 'Cox Proportional Hazards Regression'

    # Normality tests
    if 'shapiro.test(' in code_lower:
        return 'Shapiro-Wilk Normality Test'

    # Descriptive statistics
    if 'summary(' in code_lower and 'lm(' not in code_lower:
        return 'Descriptive Statistics'

    return None


def get_quick_code_summary(code: str) -> Dict[str, Any]:
    """
    Generate a quick summary of R code without using LLM.

    Useful for providing instant feedback before LLM explanation loads.

    Args:
        code: R code to summarize

    Returns:
        Dictionary with code summary information
    """
    cleaned_code = _clean_code(code)
    lines = cleaned_code.split('\n')

    # Count different elements
    comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
    code_lines = len(lines) - comment_lines
    packages = _extract_packages(cleaned_code)
    test_type = _detect_test_type(cleaned_code)

    return {
        'total_lines': len(lines),
        'code_lines': code_lines,
        'comment_lines': comment_lines,
        'packages_used': packages,
        'detected_test': test_type,
        'has_visualization': 'ggplot' in cleaned_code.lower() or 'plot(' in cleaned_code.lower()
    }


def _extract_packages(code: str) -> list:
    """Extract package names from library() or require() calls."""
    packages = []

    # Match library(package) or require(package)
    pattern = r'(?:library|require)\s*\(\s*["\']?(\w+)["\']?\s*\)'
    matches = re.findall(pattern, code)
    packages.extend(matches)

    return list(set(packages))
