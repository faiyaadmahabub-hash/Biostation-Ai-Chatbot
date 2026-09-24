"""
R Error Analyzer - Provides explanations and fix suggestions for R errors.

This module analyzes R execution errors and provides:
1. Clear explanations of why the error occurred
2. Suggested fixes with code snippets
3. Auto-fix capabilities for common errors
4. Alternative solutions when applicable
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


# Error pattern database with explanations and fixes
ERROR_PATTERNS = {
    'column_not_found': {
        'patterns': [
            r"Column [`'](\w+)[`'] is not found",
            r"object [`'](\w+)[`'] not found",
            r"undefined columns selected",
            r"column[\s\S]*?not found",
            r"Error in.*\$(\w+).*object.*not found",
        ],
        'explanation': "Your code references a column '{col}' that doesn't exist in your dataset.",
        'fix_type': 'column_replacement',
        'user_action': 'Replace the column name with one that exists in your data.'
    },

    'wide_format_error': {
        'patterns': [
            r"not all arguments have the same length",
            r"arguments imply differing number of rows",
            r"'data' must be a data frame in long format",
        ],
        'explanation': "Your data appears to be in WIDE format (each condition is a separate column), but this test expects LONG format (one row per observation).",
        'fix_type': 'reshape_data',
        'user_action': 'Add data reshaping code to convert from wide to long format.',
        'code_snippet': '''# Reshape wide to long format
library(tidyr)
data_long <- {data} %>%
  pivot_longer(
    cols = where(is.numeric),
    names_to = "condition",
    values_to = "value"
  ) %>%
  mutate(
    subject = as.factor(row_number() %% nrow({data}) + 1),
    condition = as.factor(condition)
  )
# Use data_long instead of {data} for your analysis'''
    },

    'package_not_found': {
        'patterns': [
            r"there is no package called [`'](\w+)[`']",
            r"Error in library\((\w+)\)",
            r"could not find function [`'](\w+)[`']",
        ],
        'explanation': "A required R package '{pkg}' is not installed or not loaded.",
        'fix_type': 'add_package',
        'user_action': 'Add ensure_package("{pkg}") at the top of your template.'
    },

    'grouping_factor_levels': {
        'patterns': [
            r"grouping factor must have exactly 2 levels",
            r"'x' and 'y' must have the same length",
        ],
        'explanation': "The t-test requires exactly 2 groups, but your data has more or fewer groups.",
        'fix_type': 'filter_or_switch',
        'user_action': 'Either filter your data to keep only 2 groups, or use a different test.',
        'alternatives': [
            {
                'name': 'Filter to first 2 groups',
                'description': 'Keep only the first two unique values of your grouping variable',
                'code': '{data} <- {data} %>% filter({group_var} %in% unique({group_var})[1:2])'
            },
            {
                'name': 'Use ANOVA instead',
                'description': 'For comparing 3 or more groups with normal data',
                'test': 'anova'
            },
            {
                'name': 'Use Kruskal-Wallis',
                'description': 'For comparing 3 or more groups with non-normal data',
                'test': 'kruskal_wallis'
            }
        ]
    },

    'curly_brace_error': {
        'patterns': [
            r"unexpected [`']\{[`']",
            r"unexpected [`']\}[`']",
            r"unexpected symbol",
        ],
        'explanation': "R's curly braces are conflicting with template placeholders. In templates, single braces { } are for placeholders.",
        'fix_type': 'escape_braces',
        'user_action': 'Use DOUBLE braces {{ }} for R code blocks (if/else, for loops, functions).',
        'code_snippet': '''# WRONG:
if (x > 0) { print("yes") }

# CORRECT:
if (x > 0) {{ print("yes") }}'''
    },

    'formula_error': {
        'patterns': [
            r"invalid formula",
            r"object.*is not a function",
            r"Error in model\.frame",
        ],
        'explanation': "There's an issue with your statistical formula. The formula syntax may be incorrect.",
        'fix_type': 'formula_fix',
        'user_action': 'Check that your formula uses ~ correctly: outcome ~ predictor or outcome ~ group'
    },

    'na_values': {
        'patterns': [
            r"missing values",
            r"NA/NaN/Inf",
            r"contains missing values",
        ],
        'explanation': "Your data contains missing values (NA) which this function cannot handle by default.",
        'fix_type': 'handle_na',
        'user_action': 'Add na.rm = TRUE to calculations, or remove NA rows first.',
        'code_snippet': '''# Option 1: Remove NA values from specific calculation
mean({y_var}, na.rm = TRUE)

# Option 2: Remove all rows with NA values
{data} <- na.omit({data})

# Option 3: Remove NA from specific columns
{data} <- {data} %>% filter(!is.na({y_var}))'''
    },

    'data_not_found': {
        'patterns': [
            r"object [`']data[`'] not found",
            r"Error in eval.*data",
        ],
        'explanation': "The data frame 'data' was not found. This usually means the data loading step is missing.",
        'fix_type': 'add_data_loading',
        'user_action': 'Make sure {data_loading} is at the top of your template after {package_helper}.'
    },

    'type_mismatch': {
        'patterns': [
            r"cannot coerce type",
            r"invalid 'type'",
            r"is\.numeric.*is not TRUE",
            r"must be numeric",
        ],
        'explanation': "A variable has the wrong data type. The test expects numeric data but received text/factor.",
        'fix_type': 'convert_type',
        'user_action': 'Convert your variable to the correct type.',
        'code_snippet': '''# Convert to numeric
{data}${y_var} <- as.numeric({data}${y_var})

# Convert to factor (for grouping)
{data}${group_var} <- as.factor({data}${group_var})'''
    }
}


def find_similar_column(target: str, columns: List[str]) -> Optional[str]:
    """
    Find the most similar column name using fuzzy matching.
    """
    if not columns:
        return None

    best_match = None
    best_ratio = 0.0

    target_lower = target.lower()

    for col in columns:
        # Exact match (case-insensitive)
        if col.lower() == target_lower:
            return col

        # Fuzzy match
        ratio = SequenceMatcher(None, target_lower, col.lower()).ratio()
        if ratio > best_ratio and ratio > 0.5:
            best_ratio = ratio
            best_match = col

    # If no good match, return first column as fallback
    return best_match if best_match else columns[0] if columns else None


def extract_column_name(error: str) -> Optional[str]:
    """
    Extract the column name mentioned in an error message.
    """
    patterns = [
        r"Column [`'](\w+)[`']",
        r"object [`'](\w+)[`']",
        r"\$(\w+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, error)
        if match:
            return match.group(1)

    return None


def extract_package_name(error: str) -> Optional[str]:
    """
    Extract the package name mentioned in an error message.
    """
    patterns = [
        r"package called [`'](\w+)[`']",
        r"library\((\w+)\)",
        r"function [`'](\w+)[`']",
    ]

    for pattern in patterns:
        match = re.search(pattern, error)
        if match:
            return match.group(1)

    return None


def generate_auto_fix(
    error_type: str,
    code: str,
    error_message: str,
    dataset_info: Dict[str, Any]
) -> Optional[str]:
    """
    Generate automatically fixed code based on error type.
    """
    columns = dataset_info.get('column_names', [])

    if error_type == 'column_not_found':
        missing_col = extract_column_name(error_message)
        if missing_col and columns:
            replacement = find_similar_column(missing_col, columns)
            if replacement:
                # Replace all occurrences of the missing column
                fixed_code = re.sub(
                    rf'\b{re.escape(missing_col)}\b',
                    replacement,
                    code
                )
                return fixed_code

    elif error_type == 'curly_brace_error':
        # Double-escape single braces that aren't already doubled
        fixed_code = code
        # Find if/else/for/while/function blocks and double their braces
        fixed_code = re.sub(
            r'(\b(?:if|else|for|while|function)\s*(?:\([^)]*\))?\s*)\{(?!\{)',
            r'\1{{',
            fixed_code
        )
        fixed_code = re.sub(
            r'\}(?!\})(\s*(?:else)?)',
            r'}}\1',
            fixed_code
        )
        return fixed_code

    elif error_type == 'add_package':
        pkg = extract_package_name(error_message)
        if pkg:
            # Add ensure_package after {package_helper}
            if '{package_helper}' in code:
                fixed_code = code.replace(
                    '{package_helper}',
                    f'{{package_helper}}\nensure_package("{pkg}")'
                )
            else:
                fixed_code = f'ensure_package("{pkg}")\nlibrary({pkg})\n' + code
            return fixed_code

    return None


def analyze_r_error(
    error: str,
    code: str,
    dataset_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze an R error and return structured suggestions.

    Args:
        error: The error message from R execution
        code: The R code that was executed
        dataset_info: Dictionary with 'column_names', 'filename', etc.

    Returns:
        Dictionary containing:
        {
            'error_type': str,
            'explanation': str,
            'suggestion': str,
            'fix_available': bool,
            'fix_code': Optional[str],
            'code_snippet': Optional[str],
            'alternatives': Optional[List],
            'dataset_columns': List[str]
        }
    """
    columns = dataset_info.get('column_names', [])
    filename = dataset_info.get('filename', 'your data')

    result = {
        'error_type': 'unknown',
        'explanation': f"An error occurred while running your R code: {error[:200]}",
        'suggestion': "Check your code for syntax errors or incorrect variable names.",
        'fix_available': False,
        'fix_code': None,
        'code_snippet': None,
        'alternatives': None,
        'dataset_columns': columns
    }

    # Try to match against known error patterns
    for error_type, pattern_info in ERROR_PATTERNS.items():
        for pattern in pattern_info['patterns']:
            if re.search(pattern, error, re.IGNORECASE):
                # Found a matching error pattern
                result['error_type'] = error_type

                # Build explanation with context
                explanation = pattern_info['explanation']

                # Replace placeholders in explanation
                if '{col}' in explanation:
                    col = extract_column_name(error)
                    if col:
                        explanation = explanation.replace('{col}', col)
                        explanation += f"\n\nYour dataset '{filename}' has these columns: {', '.join(columns[:10])}"
                        if len(columns) > 10:
                            explanation += f" ... and {len(columns) - 10} more"

                if '{pkg}' in explanation:
                    pkg = extract_package_name(error)
                    if pkg:
                        explanation = explanation.replace('{pkg}', pkg)

                result['explanation'] = explanation
                result['suggestion'] = pattern_info['user_action']

                # Add code snippet if available
                if 'code_snippet' in pattern_info:
                    result['code_snippet'] = pattern_info['code_snippet']

                # Add alternatives if available
                if 'alternatives' in pattern_info:
                    result['alternatives'] = pattern_info['alternatives']

                # Try to generate auto-fix
                auto_fix = generate_auto_fix(error_type, code, error, dataset_info)
                if auto_fix and auto_fix != code:
                    result['fix_available'] = True
                    result['fix_code'] = auto_fix

                logger.info(f"Analyzed error as '{error_type}': {explanation[:100]}...")
                return result

    # No specific pattern matched - provide generic advice
    logger.info(f"Could not match error to known patterns: {error[:100]}...")
    return result


def get_fix_for_template(
    error_type: str,
    template_code: str,
    error_message: str,
    dataset_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get a fix suggestion specifically for template code (before placeholder substitution).

    This is used when editing templates in the Teach modal.
    """
    columns = dataset_info.get('column_names', [])

    suggestions = []

    # Check for hardcoded column names that should be placeholders
    hardcoded_cols = re.findall(r'data\$(\w+)', template_code)
    valid_placeholders = ['y_var', 'x_var', 'group_var', 'subject_var', 'var1', 'var2']

    for col in hardcoded_cols:
        if col not in valid_placeholders and col not in ['y_var_clean', 'x_var_clean', 'group_var_clean']:
            suggestions.append({
                'issue': f"Hardcoded column name: data${col}",
                'fix': f"Use a placeholder like {{y_var}} or {{group_var}} instead",
                'severity': 'warning'
            })

    # Check for missing essential placeholders
    if '{package_helper}' not in template_code:
        suggestions.append({
            'issue': "Missing {package_helper}",
            'fix': "Add {package_helper} at the very beginning of your template",
            'severity': 'error'
        })

    if '{data_loading}' not in template_code:
        suggestions.append({
            'issue': "Missing {data_loading}",
            'fix': "Add {data_loading} after {package_helper} to load the user's data",
            'severity': 'error'
        })

    # Check for single braces in control structures
    control_patterns = [
        (r'if\s*\([^)]+\)\s*\{(?!\{)', "if statement with single brace"),
        (r'else\s*\{(?!\{)', "else statement with single brace"),
        (r'for\s*\([^)]+\)\s*\{(?!\{)', "for loop with single brace"),
    ]

    for pattern, desc in control_patterns:
        if re.search(pattern, template_code):
            suggestions.append({
                'issue': f"{desc} found",
                'fix': "Use double braces {{ }} for R control structures",
                'severity': 'warning'
            })

    return {
        'suggestions': suggestions,
        'has_errors': any(s['severity'] == 'error' for s in suggestions),
        'has_warnings': any(s['severity'] == 'warning' for s in suggestions)
    }
