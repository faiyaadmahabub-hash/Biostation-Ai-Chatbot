"""
Analysis handlers for statistical comparisons and correlations.

These handlers process user requests for group comparisons, correlation
analysis, and descriptive statistics. Each handler validates that a
dataset is loaded before attempting analysis.
"""

from typing import Any, Dict, Generator, Union

from .base import execute_and_interpret_result, get_cached_code, get_dataset_info


# Response returned when no dataset is available
_NO_DATASET_MESSAGE = (
    "**Please upload a dataset first.**\n\n"
    "I need data to perform this analysis."
)


def handle_descriptive_stats(
    interpretation: Dict[str, Any],
    client: Any
) -> Union[str, Generator[str, None, None]]:
    """
    Handle requests for descriptive statistics (mean, variance, etc.).

    Args:
        interpretation: Parsed intent containing action and parameters.
        client: LLM client for generating interpretations.

    Returns:
        Error message if no dataset, otherwise a generator yielding
        analysis results.
    """
    dataset = get_dataset_info()

    if not dataset['column_names']:
        return _NO_DATASET_MESSAGE

    code = get_cached_code(
        'descriptive',
        dataset['filepath'],
        tuple(sorted(dataset['column_names']))
    )

    return execute_and_interpret_result('descriptive', code, client, dataset['info'])


def handle_comparison(
    interpretation: Dict[str, Any],
    client: Any
) -> Union[str, Generator[str, None, None]]:
    """
    Handle requests to compare groups (t-tests, ANOVA, non-parametric).

    Automatically selects the appropriate test based on parameters in the
    interpretation dict. Defaults to unpaired t-test when test type is
    not specified.

    Args:
        interpretation: Parsed intent containing test_type parameter.
        client: LLM client for generating interpretations.

    Returns:
        Error message if no dataset, otherwise a generator yielding
        analysis results.
    """
    dataset = get_dataset_info()

    if not dataset['column_names']:
        return _NO_DATASET_MESSAGE

    test_id = _determine_comparison_test(interpretation)

    code = get_cached_code(
        test_id,
        dataset['filepath'],
        tuple(sorted(dataset['column_names']))
    )

    return execute_and_interpret_result(test_id, code, client, dataset['info'])


def _determine_comparison_test(interpretation: Dict[str, Any]) -> str:
    """
    Map user's test type specification to internal test ID.

    Uses keyword matching to identify the intended test. Falls back to
    unpaired t-test as the most common comparison scenario.
    """
    params = interpretation.get('parameters', {})
    test_type = params.get('test_type', '')

    if not test_type:
        return 'unpaired_ttest'

    test_type_lower = test_type.lower()

    # Check for two-way/factorial ANOVA first (more specific)
    if 'two' in test_type_lower and 'way' in test_type_lower:
        return 'two_way_anova'
    if 'factorial' in test_type_lower:
        return 'two_way_anova'

    # Then check for one-way ANOVA
    if 'anova' in test_type_lower:
        return 'anova'

    # Non-parametric alternatives
    if 'mann' in test_type_lower:
        return 'mann_whitney'

    # Paired designs
    if 'paired' in test_type_lower:
        return 'paired_ttest'

    return 'unpaired_ttest'


# Note: Correlation handlers have been moved to handlers/correlation.py
# for better modularity. Import from there for handle_correlation and
# handle_correlation_matrix.
