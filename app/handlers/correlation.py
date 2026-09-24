"""
Correlation handlers for correlation analysis including correlation matrix.

This module handles requests for:
- Pairwise correlations (Pearson, Spearman)
- Correlation matrix with heatmap visualization
"""

from typing import Any, Dict, Generator, Union

from .base import execute_and_interpret_result, get_cached_code, get_dataset_info


# Response returned when no dataset is available
_NO_DATASET_MESSAGE = (
    "**Please upload a dataset first.**\n\n"
    "I need data to perform correlation analysis."
)

# Message when not enough numeric columns
_NOT_ENOUGH_COLUMNS_MESSAGE = (
    "**Not enough numeric columns for correlation matrix.**\n\n"
    "A correlation matrix requires at least 2 numeric columns in your dataset."
)


def handle_correlation(
    interpretation: Dict[str, Any],
    client: Any
) -> Union[str, Generator[str, None, None]]:
    """
    Handle requests for pairwise correlation analysis.

    Supports both Pearson and Spearman correlations based on user request.

    Args:
        interpretation: Parsed intent containing correlation type parameter.
        client: LLM client for generating interpretations.

    Returns:
        Error message if no dataset, otherwise a generator yielding
        analysis results.
    """
    dataset = get_dataset_info()

    if not dataset['column_names']:
        return _NO_DATASET_MESSAGE

    # Determine correlation method
    test_id = _determine_correlation_type(interpretation)

    code = get_cached_code(
        test_id,
        dataset['filepath'],
        tuple(sorted(dataset['column_names']))
    )

    return execute_and_interpret_result(test_id, code, client, dataset['info'])


def handle_correlation_matrix(
    interpretation: Dict[str, Any],
    client: Any
) -> Union[str, Generator[str, None, None]]:
    """
    Handle requests for correlation matrix with heatmap visualization.

    Generates a correlation matrix for all numeric columns in the dataset,
    including p-values and significance indicators.

    Args:
        interpretation: Parsed intent containing method preference.
        client: LLM client for generating interpretations.

    Returns:
        Error message if no dataset or insufficient columns, otherwise
        a generator yielding analysis results with heatmap.
    """
    dataset = get_dataset_info()

    if not dataset['column_names']:
        return _NO_DATASET_MESSAGE

    # Check if we have enough numeric columns (basic check)
    # The R code will do a more thorough check
    if len(dataset['column_names']) < 2:
        return _NOT_ENOUGH_COLUMNS_MESSAGE

    # Determine correlation method (Pearson or Spearman)
    method = _extract_correlation_method(interpretation)

    # Generate code with method parameter
    from app.code_gen.template_loader import get_template_loader
    loader = get_template_loader()

    variables = {
        'correlation_method': method
    }

    code = loader.generate_code(
        'correlation_matrix',
        dataset['filepath'],
        variables
    )

    return execute_and_interpret_result(
        'correlation_matrix', code, client, dataset['info']
    )


def _determine_correlation_type(interpretation: Dict[str, Any]) -> str:
    """
    Determine which correlation test to use based on user request.

    Defaults to Pearson correlation unless Spearman is explicitly requested.
    """
    params = interpretation.get('parameters', {})
    query = interpretation.get('query', '').lower()

    # Check for explicit Spearman request
    if 'spearman' in query or params.get('method', '').lower() == 'spearman':
        return 'spearman_correlation'

    return 'pearson_correlation'


def _extract_correlation_method(interpretation: Dict[str, Any]) -> str:
    """
    Extract the correlation method preference from user request.

    Returns 'pearson' or 'spearman' based on user specification.
    Defaults to 'pearson'.
    """
    params = interpretation.get('parameters', {})
    query = interpretation.get('query', '').lower()

    # Check for explicit Spearman request
    if 'spearman' in query or params.get('method', '').lower() == 'spearman':
        return 'spearman'

    return 'pearson'
