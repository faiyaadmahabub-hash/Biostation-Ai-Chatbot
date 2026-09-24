"""
Handlers module for the BioStation chat system.

This module provides centralized request handlers organized by domain:

- **Test Selection**: Guided decision-tree-based test recommendation
- **Analysis**: Statistical comparisons, correlations, descriptive stats
- **Code Generation**: R code generation for statistical tests
- **Debugging**: R error parsing and explanation
- **Explanation**: Educational content about statistical methods
- **General**: Fallback LLM-based responses

Example:
    from app.handlers import handle_comparison, handle_explanation

    # Route a comparison request
    result = handle_comparison(interpretation, llm_client)

    # Get an explanation
    explanation = handle_explanation("What is ANOVA?", llm_client)
"""

# Base utilities shared across handlers
from .base import (
    TEST_MAPPING,
    get_cached_code,
    get_dataset_info,
    execute_and_interpret_result,
)

# Test selection handler
from .test_selection import handle_test_selection

# Statistical analysis handlers
from .analysis import (
    handle_comparison,
    handle_descriptive_stats,
)

# Correlation analysis handlers
from .correlation import (
    handle_correlation,
    handle_correlation_matrix,
)

# Code generation handler
from .code_generation import handle_code_generation

# Code explanation handler
from .code_explanation import handle_code_explanation, get_quick_code_summary

# Error debugging handler
from .debugging import handle_error_debug

# Educational explanation handlers
from .explanation import (
    handle_explanation,
    handle_post_hoc,
)

# General/fallback handler
from .general import handle_general


__all__ = [
    # Base utilities
    'TEST_MAPPING',
    'get_cached_code',
    'get_dataset_info',
    'execute_and_interpret_result',
    # Primary handlers
    'handle_test_selection',
    'handle_comparison',
    'handle_correlation',
    'handle_correlation_matrix',
    'handle_descriptive_stats',
    'handle_code_generation',
    'handle_code_explanation',
    'get_quick_code_summary',
    'handle_error_debug',
    'handle_explanation',
    'handle_post_hoc',
    'handle_general',
]
