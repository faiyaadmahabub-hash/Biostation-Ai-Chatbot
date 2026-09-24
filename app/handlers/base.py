"""
Base handler utilities for the chat system.

This module provides shared constants, caching utilities, and the core
R code execution pipeline used by all analysis handlers. Centralizing
these utilities ensures consistent behavior across handlers and enables
efficient code caching.
"""

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any, Dict, Generator, Optional

from flask import session

from app.code_gen import code_generator
from app.r_engine import output_parser, r_executor

logger = logging.getLogger(__name__)

# Thread pool size chosen to balance parallelism with R's memory usage.
# R processes can be memory-intensive, so we limit concurrent executions.
_R_EXECUTOR_POOL = ThreadPoolExecutor(max_workers=3, thread_name_prefix="r_exec")

# Maximum retry attempts for auto-debugging failed R code.
# Two retries provides reasonable error recovery without excessive LLM calls.
_MAX_AUTO_DEBUG_RETRIES = 2

# Output truncation limits to prevent token overflow in LLM prompts.
_MAX_OUTPUT_FOR_LLM = 2000
_MAX_OUTPUT_FOR_DISPLAY = 1000

# Canonical mapping from user-friendly test names to internal test IDs.
# This enables flexible natural language input while maintaining consistent
# internal identifiers for code generation and knowledge lookup.
_BUILTIN_TEST_MAPPING = {
    # T-tests
    't-test': 'unpaired_ttest',
    'ttest': 'unpaired_ttest',
    'paired t': 'paired_ttest',
    'one sample': 'one_sample_ttest',
    'one sample t': 'one_sample_ttest',
    # ANOVA variants
    'anova': 'anova',
    'two-way anova': 'two_way_anova',
    'two way anova': 'two_way_anova',
    'factorial anova': 'two_way_anova',
    'two-way': 'two_way_anova',
    'two way': 'two_way_anova',
    'factorial': 'two_way_anova',
    'interaction': 'two_way_anova',
    # Non-parametric tests
    'mann-whitney': 'mann_whitney',
    'mann whitney': 'mann_whitney',
    'wilcoxon': 'wilcoxon_signed_rank',
    'kruskal': 'kruskal_wallis',
    # Multiple comparison corrections (mapped to single ID for routing)
    'multiple comparison': 'multiple_comparison',
    'bonferroni': 'multiple_comparison',
    'holm': 'multiple_comparison',
    'fdr': 'multiple_comparison',
    'tukey': 'multiple_comparison',
    'post-hoc': 'multiple_comparison',
    'post hoc': 'multiple_comparison',
    'posthoc': 'multiple_comparison',
    # Correlation
    'pearson': 'pearson_correlation',
    'spearman': 'spearman_correlation',
    # Categorical tests
    'chi-squared': 'chi_squared',
    'chi squared': 'chi_squared',
    'fisher': 'fisher_exact',
    # Regression
    'regression': 'linear_regression',
    'linear regression': 'linear_regression',
    'glm': 'glm',
    'logistic': 'glm',
    'glmm': 'glmm',
    'gam': 'gam',
    # Descriptive statistics
    'mean': 'descriptive',
    'variance': 'descriptive',
    'summary': 'descriptive',
}

# Cache for merged test mapping (built-in + custom)
_merged_test_mapping = None


def get_test_mapping() -> Dict[str, str]:
    """
    Get the full test mapping including custom user-taught tests.
    Merges built-in mappings with custom test keywords.
    """
    global _merged_test_mapping
    if _merged_test_mapping is None:
        _merged_test_mapping = _BUILTIN_TEST_MAPPING.copy()
        try:
            from app.guidebook.dynamic_loader import get_custom_test_keywords_mapping
            custom_mapping = get_custom_test_keywords_mapping()
            _merged_test_mapping.update(custom_mapping)
            if custom_mapping:
                logger.info(f"Loaded {len(custom_mapping)} custom test keywords")
        except ImportError:
            logger.warning("Could not import custom test mappings")
    return _merged_test_mapping


def refresh_test_mapping():
    """Force refresh of test mapping to pick up new custom tests."""
    global _merged_test_mapping
    _merged_test_mapping = None


def clear_code_cache():
    """Clear the R code generation cache to pick up template changes."""
    _cached_code_impl.cache_clear()
    logger.info("Cleared R code generation cache")


# For backwards compatibility, expose TEST_MAPPING as a property-like access
# Code should use get_test_mapping() for dynamic access
TEST_MAPPING = _BUILTIN_TEST_MAPPING  # Static reference for imports


@lru_cache(maxsize=128)
def _cached_code_impl(test_id: str, data_source: str, columns_tuple: tuple) -> str:
    """Internal cached code generation for built-in tests."""
    return code_generator.generate_code(
        test_id,
        data_source=data_source,
        column_context=list(columns_tuple)
    )


def get_cached_code(test_id: str, data_source: str, columns_tuple: tuple) -> str:
    """
    Generate R code with LRU caching for built-in tests.
    Custom tests (starting with 'custom_') always regenerate fresh code.

    The cache key includes the test type, data source path, and column set,
    so identical requests return cached code instantly while any change in
    parameters triggers fresh generation.

    Args:
        test_id: Internal identifier for the statistical test.
        data_source: File path or data frame reference for R code.
        columns_tuple: Tuple of column names (must be tuple for hashability).

    Returns:
        Generated R code as a string.
    """
    # Skip cache for custom tests - they may be modified by users
    if test_id.startswith('custom_'):
        return code_generator.generate_code(
            test_id,
            data_source=data_source,
            column_context=list(columns_tuple)
        )

    return _cached_code_impl(test_id, data_source, columns_tuple)


def get_dataset_info() -> Dict[str, Any]:
    """
    Retrieve current dataset metadata from the Flask session.

    Returns a normalized dictionary with guaranteed keys, using sensible
    defaults when no dataset is loaded. The filepath is normalized to
    forward slashes for R compatibility on Windows.

    Returns:
        Dictionary containing:
            - info: Raw session dataset dict
            - column_names: List of column names (may be empty)
            - filename: Display name for the file
            - filepath: R-compatible path string
    """
    dataset_info = session.get('current_dataset', {})
    raw_filepath = dataset_info.get('filepath', 'your_data.csv')

    return {
        'info': dataset_info,
        'column_names': dataset_info.get('column_names', []),
        'filename': dataset_info.get('filename', 'your_data.csv'),
        'filepath': raw_filepath.replace('\\', '/')
    }


def execute_and_interpret_result(
    test_id: str,
    code: str,
    client: Any,
    dataset_info: Dict[str, Any],
    retry_count: int = 0
) -> Generator[str, None, None]:
    """
    Execute R code and generate an LLM interpretation of results.

    This is a generator that yields response chunks for streaming support.
    It implements automatic error recovery by asking the LLM to fix common
    R errors (up to MAX_AUTO_DEBUG_RETRIES attempts).

    Args:
        test_id: Internal identifier for the statistical test.
        code: R code to execute.
        client: LLM client instance for generating interpretations.
        dataset_info: Dictionary containing dataset metadata.
        retry_count: Current retry attempt (internal use for recursion).

    Yields:
        Markdown-formatted response chunks suitable for streaming to the client.
    """
    # Import here to avoid circular dependency
    from app.advisor.test_knowledge import get_test_info

    # Check custom tests first, then built-in tests
    custom_context = _get_custom_test_context(test_id)
    if custom_context:
        test_name = custom_context.get('name', test_id.replace('_', ' ').title())
        purpose = custom_context.get('purpose', 'statistical analysis')
    else:
        test_info = get_test_info(test_id)
        test_name = test_info.name if test_info else test_id.replace('_', ' ').title()
        purpose = test_info.purpose if test_info else "statistical analysis"

    # Yield introduction immediately for responsive UX
    yield f"Running **{test_name}** analysis.\n\n**Purpose**: {purpose}.\n\n"
    yield f"## R Code\n```r\n{code}\n```\n\n"

    # Execute in thread pool to avoid blocking the request thread
    logger.info("Executing R code for %s (attempt %d)", test_id, retry_count + 1)
    future = _R_EXECUTOR_POOL.submit(r_executor.execute, code, True)
    result = future.result()

    # Auto-debug loop: attempt LLM-assisted code correction on failure
    if not result.success and retry_count < _MAX_AUTO_DEBUG_RETRIES:
        logger.info(
            "R execution failed, attempting auto-debug (retry %d/%d). Error: %s",
            retry_count + 1, _MAX_AUTO_DEBUG_RETRIES, result.errors
        )

        corrected_code = _attempt_code_fix(code, result.errors, dataset_info, client)
        if corrected_code:
            yield from execute_and_interpret_result(
                test_id, corrected_code, client, dataset_info,
                retry_count=retry_count + 1
            )
            return

    # Build final response based on execution outcome
    yield from _format_execution_results(test_id, result, client, retry_count)


def _attempt_code_fix(
    code: str,
    error_message: str,
    dataset_info: Dict[str, Any],
    client: Any
) -> Optional[str]:
    """
    Ask the LLM to fix R code that failed to execute.

    Returns the corrected code if extraction succeeds, None otherwise.
    """
    col_list = dataset_info.get('column_names', [])

    debug_prompt = f"""You are an expert R debugger.
The following R code failed to execute on the user's dataset.

Code:
```r
{code}
```

Error Message:
{error_message}

Dataset Info:
Columns: {col_list}

Task: Fix the R code to resolve the error.
Specific Fixes:
- If error is "grouping factor must have exactly 2 levels": Filter data to keep only the first two unique values of the grouping variable.
  Example: data <- subset(data, GroupVar %in% unique(data$GroupVar)[1:2])
- If columns are missing/wrong: Use the provided column list to identify correct names.
- Preserve the file path in read.csv.

Output: Return ONLY the corrected R code block (inside ```r ... ```)."""

    fix_response = client.generate(debug_prompt, temperature=0.2)

    # Extract R code block from LLM response
    match = re.search(r"```r\n(.*?)\n```", fix_response, re.DOTALL)
    return match.group(1) if match else None


def _format_execution_results(
    test_id: str,
    result: Any,
    client: Any,
    retry_count: int
) -> Generator[str, None, None]:
    """
    Format R execution results into markdown for display.

    Generates LLM interpretation for successful runs, or error details
    for failed executions.
    """
    if result.success:
        status = "**Analysis completed successfully.**"
        if retry_count > 0:
            status += f" (Auto-corrected after {retry_count} attempt{'s' if retry_count > 1 else ''})"

        interpretation = _generate_interpretation(test_id, result.output, client)
    else:
        status = "**Analysis failed.**"
        interpretation = (
            f"The code could not be executed after {retry_count + 1} attempts.\n\n"
            f"Error: `{result.errors}`"
        )

    # Format plot references if any were generated
    plot_section = ""
    if result.plots:
        for plot_path in result.plots:
            filename = os.path.basename(plot_path)
            plot_section += f"\n\n![Result Plot](/api/plot/{filename})\n"

    # Truncate output for display to prevent overwhelming the UI
    truncated_output = result.output[:_MAX_OUTPUT_FOR_DISPLAY]
    if len(result.output) > _MAX_OUTPUT_FOR_DISPLAY:
        truncated_output += "..."

    yield f"""## Execution Results
{status}

```text
{truncated_output}
```
{plot_section}

## Interpretation
{interpretation}
"""


def _generate_interpretation(test_id: str, output: str, client: Any) -> str:
    """
    Generate a plain-language interpretation of R output using the LLM.

    OPTIMIZED FOR BIOSCIENCE STUDENTS:
    - Educational explanations suitable for biology/life sciences students
    - Includes assumptions and conditions for the statistical test
    - Uses custom test explanation if available
    - Uses cached generation for instant results on repeated queries
    - Lower temperature (0.1) for deterministic, faster sampling
    """
    # Truncate output to stay within token limits
    safe_output = output[:_MAX_OUTPUT_FOR_LLM]

    # Get test-specific assumptions
    assumptions_context = _get_test_assumptions(test_id)

    # Get custom test explanation context if available
    custom_context = _get_custom_test_context(test_id)
    interpretation_guide = ""
    if custom_context and custom_context.get('explanation'):
        interpretation_guide = f"""
Use the following educational context about this test when forming your interpretation:

{custom_context['explanation']}

"""

    system_prompt = """You are a biostatistics educator helping biology and life sciences students understand statistical results.
Provide clear, educational interpretations that explain both the statistical outcome AND its biological/scientific meaning.
Always include the assumptions and conditions required for the test to be valid.
Use simple language but be thorough enough for learning."""

    user_prompt = f"""{interpretation_guide}Interpret this {test_id} test output for bioscience students:

{safe_output}

Provide a comprehensive interpretation with these sections:

- **Statistical Conclusion:** Explain whether results are significant/not significant with p-value and test statistic
- **Biological/Scientific Meaning:** What this means in biological/scientific terms
- **Importance:** Brief explanation of why this matters for research (3-4 sentences)

**Assumptions & Conditions:**
{assumptions_context}
List the key assumptions that must be met for this test to be valid, and briefly explain each one in the context of biological data.

Format all section headers in bold using ** markers."""

    # Use cached generation for instant repeated queries (5-min cache)
    # Increased token limit (768) for interpretation + assumptions
    return client.generate_cached(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.1,  # Deterministic for consistent educational content
        max_tokens=768    # Increased for interpretation + assumptions
    )


def _get_custom_test_context(test_id: str) -> Optional[Dict[str, str]]:
    """
    Get explanation and assumptions from a custom test.
    Returns dict with 'explanation' and 'assumptions' keys, or None if not a custom test.
    """
    try:
        from app.guidebook.dynamic_loader import get_custom_test
        custom_test = get_custom_test(test_id)
        if custom_test:
            return {
                'explanation': custom_test.get('explanation', ''),
                'assumptions': custom_test.get('assumptions', ''),
                'name': custom_test.get('name', test_id),
                'purpose': custom_test.get('purpose', 'statistical analysis')
            }
    except ImportError:
        pass
    return None


def _get_test_assumptions(test_id: str) -> str:
    """
    Get the key assumptions for a specific statistical test.
    Checks custom tests first, then falls back to built-in assumptions.
    Returns context string to guide the LLM in explaining assumptions.
    """
    # Check custom tests first
    custom_context = _get_custom_test_context(test_id)
    if custom_context and custom_context.get('assumptions'):
        return f"""
Based on the following assumptions provided for this test:

{custom_context['assumptions']}

Explain these assumptions in the context of biological data and why they matter."""

    # Built-in assumptions
    assumptions = {
        'pearson_correlation': """
For Pearson Correlation, the key assumptions are:
1. Linearity - The relationship between variables should be linear
2. Normality - Both variables should be approximately normally distributed
3. Homoscedasticity - Equal variance across the range of data
4. Continuous data - Both variables should be continuous (interval/ratio scale)
5. No significant outliers - Outliers can heavily influence the correlation coefficient
6. Independence - Observations should be independent of each other""",

        'spearman_correlation': """
For Spearman Correlation, the key assumptions are:
1. Monotonic relationship - Variables should have a monotonic relationship (not necessarily linear)
2. Ordinal or continuous data - Both variables should be at least ordinal scale
3. Independence - Observations should be independent of each other
4. No assumption of normality - More robust to non-normal distributions""",

        'unpaired_ttest': """
For Independent Samples T-Test, the key assumptions are:
1. Independence - Observations in each group are independent
2. Normality - Data in each group should be approximately normally distributed
3. Homogeneity of variance - Both groups should have similar variances
4. Continuous data - The dependent variable should be continuous
5. Random sampling - Data should be randomly sampled from the population""",

        'paired_ttest': """
For Paired Samples T-Test, the key assumptions are:
1. Paired observations - Each observation in one group is paired with one in the other
2. Normality of differences - The differences between pairs should be normally distributed
3. Continuous data - The dependent variable should be continuous
4. Independence of pairs - Each pair should be independent of other pairs
5. Random sampling - Pairs should be randomly selected""",

        'anova': """
For One-Way ANOVA, the key assumptions are:
1. Independence - Observations are independent within and between groups
2. Normality - Data in each group should be approximately normally distributed
3. Homogeneity of variance - All groups should have similar variances (Levene's test)
4. Continuous data - The dependent variable should be continuous
5. Random sampling - Data should be randomly sampled from populations""",

        'two_way_anova': """
For Two-Way ANOVA, the key assumptions are:
1. Independence - Observations are independent
2. Normality - Residuals should be normally distributed
3. Homogeneity of variance - Equal variances across all groups
4. Continuous data - The dependent variable should be continuous
5. No significant interaction (if testing main effects) - Or interaction should be interpreted
6. Balanced design preferred - Equal sample sizes in each cell""",

        'chi_squared': """
For Chi-Squared Test, the key assumptions are:
1. Categorical data - Both variables should be categorical
2. Independence - Observations should be independent
3. Expected frequencies - Expected count in each cell should be at least 5
4. Mutually exclusive categories - Each observation belongs to only one category
5. Random sampling - Data should be randomly sampled""",

        'mann_whitney': """
For Mann-Whitney U Test, the key assumptions are:
1. Independence - Observations are independent between groups
2. Ordinal or continuous data - The dependent variable should be at least ordinal
3. Similar distribution shapes - Both groups should have similarly shaped distributions
4. Random sampling - Data should be randomly sampled
5. No assumption of normality - Non-parametric alternative to t-test""",

        'kruskal_wallis': """
For Kruskal-Wallis Test, the key assumptions are:
1. Independence - Observations are independent
2. Ordinal or continuous data - The dependent variable should be at least ordinal
3. Similar distribution shapes - All groups should have similarly shaped distributions
4. Random sampling - Data should be randomly sampled
5. No assumption of normality - Non-parametric alternative to ANOVA""",

        'linear_regression': """
For Linear Regression, the key assumptions are:
1. Linearity - The relationship between X and Y is linear
2. Independence - Observations are independent
3. Homoscedasticity - Constant variance of residuals
4. Normality of residuals - Residuals should be normally distributed
5. No multicollinearity - Predictors should not be highly correlated (for multiple regression)
6. No influential outliers - Outliers can distort the regression line""",

        'wilcoxon_signed_rank': """
For Wilcoxon Signed-Rank Test, the key assumptions are:
1. Paired observations - Data comes in matched pairs
2. Ordinal or continuous data - Differences should be at least ordinal
3. Symmetry of differences - Distribution of differences should be symmetric
4. Independence of pairs - Each pair is independent of other pairs
5. No assumption of normality - Non-parametric alternative to paired t-test""",
    }

    # Return specific assumptions or a generic prompt
    return assumptions.get(test_id, f"""
For this {test_id} test, explain the key statistical assumptions that must be met for the test results to be valid.
Consider assumptions about data distribution, independence, measurement scale, and sample characteristics.""")
