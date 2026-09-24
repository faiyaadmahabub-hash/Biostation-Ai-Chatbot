"""
R Code Generator - Creates ready-to-run R code for statistical analyses

This module now delegates to TemplateLoader for template management.
All R templates are stored as separate .r files in app/code_gen/templates/
"""

from typing import Dict, Optional
from app.code_gen.template_loader import TemplateLoader


class RCodeGenerator:
    """
    Generates R code for statistical tests.

    This is a thin wrapper around TemplateLoader that maintains backward
    compatibility with the original API while using the new template system.
    """

    def __init__(self):
        """Initialize the code generator with template loader"""
        self.loader = TemplateLoader()
        # Keep templates property for backward compatibility
        # (in case any code checks if test_id in generator.templates)
        self.templates = {test_id: True for test_id in self.loader.TEMPLATE_MAP.keys()}
    
    def generate_code(
        self,
        test_id: str,
        data_source: str = "your_data.csv",
        variables: Dict[str, str] = None,
        parameters: Dict[str, str] = None,
        column_context: list = None
    ) -> str:
        """
        Generate R code for a specific test.

        This method maintains the original API but delegates to TemplateLoader.

        Args:
            test_id: ID of the statistical test
            data_source: Path to data file or data frame name
            variables: Dict mapping variable roles to column names
            parameters: Additional parameters (e.g., mu for one-sample t-test)
            column_context: List of actual column names from the dataset (optional)

        Returns:
            Complete R code as string
        """
        # Check if template exists
        if not self.loader.template_exists(test_id):
            return f"# Error: No template available for {test_id}"

        # Default variable mappings
        vars = variables or {}
        params = parameters or {}

        # Intelligent column guessing if context is provided but vars are empty
        if column_context and not vars:
            # Simple heuristic: take first column as outcome (y), second as predictor (x/group)
            if len(column_context) > 0:
                vars["y"] = f"data${column_context[-1]}"  # Often last col is outcome
                vars["y_name"] = column_context[-1]
                vars["y_clean"] = column_context[-1]

            if len(column_context) > 1:
                # Normal 1-variable tests
                vars["x"] = f"data${column_context[0]}"
                vars["x_name"] = column_context[0]
                vars["group"] = f"data${column_context[0]}"
                vars["group_name"] = column_context[0]

                # Special handling for Two-Way ANOVA (needs 2 factors)
                if test_id == 'two_way_anova' and len(column_context) > 2:
                    vars["x"] = f"data${column_context[0]}"
                    vars["x_name"] = column_context[0]
                    vars["x_clean"] = column_context[0]

                    vars["group"] = f"data${column_context[1]}"
                    vars["group_name"] = column_context[1]
                    vars["group_clean"] = column_context[1]

            # Repeated measures tests need a subject identifier
            # Custom tests starting with 'custom_' that mention "repeated" or "friedman"
            is_repeated_measures = (
                test_id.startswith('custom_') or
                'friedman' in test_id.lower() or
                'repeated' in test_id.lower()
            )
            if is_repeated_measures and len(column_context) >= 3:
                # For repeated measures: col[0] = subject, col[1] = condition, col[-1] = value
                vars["subject"] = column_context[0]
                vars["group"] = f"data${column_context[1]}"
                vars["group_name"] = column_context[1]
                vars["y"] = f"data${column_context[-1]}"
                vars["y_name"] = column_context[-1]

        # Merge parameters into variables for template filling
        merged_vars = {**vars, **params}

        # Use TemplateLoader to generate the code
        try:
            code = self.loader.generate_code(
                test_id=test_id,
                data_source=data_source,
                variables=merged_vars
            )
            return code
        except Exception as e:
            return f"# Error generating code for {test_id}: {str(e)}"


# Singleton instance
code_generator = RCodeGenerator()
