"""
Code generation handler for producing R statistical analysis code.

This handler processes requests to generate R code for various statistical
tests. It uses keyword matching against TEST_MAPPING to identify the
requested test type and generates context-aware code using the user's
dataset information.
"""

from typing import Any, Generator, Union

from .base import (
    get_test_mapping,
    execute_and_interpret_result,
    get_cached_code,
    get_dataset_info,
)


def handle_code_generation(
    message: str,
    client: Any
) -> Union[str, Generator[str, None, None]]:
    """
    Handle requests to generate R code for statistical analysis.

    Parses the user message to identify the requested test type, then
    either generates static code (for descriptive stats) or executes
    the analysis pipeline (for inferential tests).

    Args:
        message: User's request message.
        client: LLM client for generating interpretations.

    Returns:
        Markdown-formatted response with R code, or a generator for
        streaming analysis results.
    """
    message_lower = message.lower()
    test_id = _extract_test_id(message_lower)
    dataset = get_dataset_info()

    # Handle descriptive statistics as a special case with inline code
    if _is_descriptive_request(test_id, message_lower):
        return _generate_descriptive_code(dataset)

    # If no specific test identified, show available options
    if not test_id:
        return _generate_test_menu(dataset)

    # Generate and execute code for the identified test
    code = get_cached_code(
        test_id,
        dataset['filepath'],
        tuple(sorted(dataset['column_names']))
    )

    return execute_and_interpret_result(test_id, code, client, dataset['info'])


def _extract_test_id(message_lower: str) -> str:
    """
    Extract test ID from message using keyword matching.

    Checks both built-in and custom user-taught tests.
    Returns empty string if no match found.
    """
    test_mapping = get_test_mapping()
    for keyword, test_id in test_mapping.items():
        if keyword in message_lower:
            return test_id
    return ''


def _is_descriptive_request(test_id: str, message_lower: str) -> bool:
    """
    Check if the request is for descriptive statistics.

    Descriptive stats are handled separately because they produce
    static code rather than executing an analysis pipeline.
    """
    if test_id == 'descriptive':
        return True

    descriptive_keywords = ['mean', 'variance', 'summary', 'statistics']
    return any(word in message_lower for word in descriptive_keywords)


def _generate_descriptive_code(dataset: dict) -> str:
    """
    Generate R code for descriptive statistics with dataset context.

    Returns a message prompting for data upload if no dataset is loaded.
    """
    if not dataset['column_names']:
        return (
            "Please upload a dataset first. Then I can generate code "
            "with your actual column names.\n\n"
            "Click the attach button to upload a CSV or Excel file."
        )

    columns = dataset['column_names']
    group_col = columns[0] if columns else 'GroupColumn'
    value_col = columns[-1] if len(columns) > 1 else 'ValueColumn'

    code = f'''# Load your data
data <- read.csv("{dataset['filepath']}")

# View column names
names(data)

# Summary statistics for all columns
summary(data)

# Your columns: {', '.join(columns)}

# Calculate mean and variance for each numeric column
library(dplyr)

# Group statistics
# Modify group_by() and column names to match your analysis needs
# Available columns: {', '.join(columns)}

stats_by_group <- data %>%
  group_by({group_col}) %>%
  summarise(
    Mean = mean({value_col}, na.rm = TRUE),
    Variance = var({value_col}, na.rm = TRUE),
    SD = sd({value_col}, na.rm = TRUE),
    N = n()
  )

print(stats_by_group)
'''

    return f"""## Descriptive Statistics Code

Your uploaded file **{dataset['filename']}** has these columns:
`{', '.join(columns)}`

```r
{code}
```

**Tip**: Modify the `group_by()` and column names to match your analysis needs."""


def _generate_test_menu(dataset: dict) -> str:
    """
    Generate a menu of available statistical tests.

    Includes dataset context if a file is loaded.
    """
    test_list = """
**Available tests:**
- **T-tests**: one-sample, paired, unpaired (independent samples)
- **ANOVA**: one-way ANOVA with Tukey post-hoc
- **Non-parametric**: Mann-Whitney, Wilcoxon, Kruskal-Wallis
- **Correlation**: Pearson, Spearman
- **Categorical**: Chi-squared, Fisher's exact
- **Regression**: Linear, GLM (logistic/Poisson)
- **Descriptive**: Mean, variance, summary statistics

Say something like "Generate code for Mann-Whitney test" or "t-test code"."""

    if dataset['column_names']:
        return f"""I see you have uploaded **{dataset['filename']}** with columns:
`{', '.join(dataset['column_names'])}`

**Which statistical test would you like code for?**
{test_list}"""
    else:
        return f"Which statistical test would you like code for?\n{test_list}"
