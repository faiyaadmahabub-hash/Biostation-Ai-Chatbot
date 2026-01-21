"""
Error Parser - Parses R error messages and provides context
"""

import re
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class ParsedError:
    """Structured representation of an R error"""
    error_type: str
    error_message: str
    line_number: Optional[int]
    function_name: Optional[str]
    likely_cause: str
    suggestions: List[str]


class RErrorParser:
    """Parses R error messages and provides helpful context"""
    
    # Common R error patterns
    ERROR_PATTERNS = {
        "object_not_found": {
            "pattern": r"object '(\w+)' not found",
            "type": "Object Not Found",
            "cause": "The variable or object '{match}' doesn't exist in your environment.",
            "suggestions": [
                "Check the spelling of the variable name",
                "Make sure you've loaded your data with read.csv() or similar",
                "Check if the column name exists in your dataset using names(data)",
                "Remember R is case-sensitive: 'Data' ≠ 'data'"
            ]
        },
        "undefined_columns": {
            "pattern": r"undefined columns selected|subscript out of bounds",
            "type": "Column Selection Error",
            "cause": "You're trying to access a column that doesn't exist in the data frame.",
            "suggestions": [
                "Use names(data) to see available column names",
                "Check for typos in column names",
                "Make sure you're using $ or [[ ]] correctly"
            ]
        },
        "non_numeric": {
            "pattern": r"'x' must be numeric|requires numeric|non-numeric argument",
            "type": "Data Type Error",
            "cause": "The function expects numeric data but received text or other non-numeric values.",
            "suggestions": [
                "Check your data type with class(your_variable)",
                "Convert to numeric: as.numeric(your_variable)",
                "Check for text values like 'NA' (should be just NA)",
                "Remove or convert non-numeric entries"
            ]
        },
        "missing_package": {
            "pattern": r"there is no package called '(\w+)'",
            "type": "Missing Package",
            "cause": "The package '{match}' is not installed.",
            "suggestions": [
                "Install the package: install.packages('{match}')",
                "Then load it: library({match})"
            ]
        },
        "function_not_found": {
            "pattern": r"could not find function \"(\w+)\"",
            "type": "Function Not Found",
            "cause": "The function '{match}' is not available.",
            "suggestions": [
                "Check if the required package is loaded with library()",
                "Check the spelling of the function name",
                "The function might be in a package you haven't installed"
            ]
        },
        "formula_error": {
            "pattern": r"invalid formula|object '~' not found|invalid 'formula'",
            "type": "Formula Error",
            "cause": "There's a problem with the formula syntax (e.g., y ~ x).",
            "suggestions": [
                "Check formula syntax: outcome ~ predictor",
                "Make sure variable names match column names exactly",
                "Don't put quotes around variable names in formulas"
            ]
        },
        "dimension_mismatch": {
            "pattern": r"arguments imply differing number of rows|replacement has|length",
            "type": "Dimension Mismatch",
            "cause": "The data you're combining have different lengths or dimensions.",
            "suggestions": [
                "Check that all vectors have the same length",
                "Use length() to verify sizes match",
                "Check for NA values that might be filtered out"
            ]
        },
        "na_values": {
            "pattern": r"missing values|NaN|NA|na.rm",
            "type": "Missing Values",
            "cause": "Your data contains missing values (NA) that the function can't handle.",
            "suggestions": [
                "Add na.rm = TRUE to remove NAs: mean(x, na.rm = TRUE)",
                "Filter out NAs first: data <- na.omit(data)",
                "Check where NAs are: which(is.na(data))"
            ]
        },
        "sample_size": {
            "pattern": r"not enough.*observations|sample size|at least|fewer than|sample is too|must have",
            "type": "Sample Size Error",
            "cause": "Your sample size is too small for this analysis.",
            "suggestions": [
                "Check the sample size requirement for this test",
                "Consider a different test suitable for small samples",
                "Shapiro-Wilk requires 3-5000 observations",
                "Some tests need minimum observations per group"
            ]
        },
        "syntax_error": {
            "pattern": r"unexpected|parse error|Error in parse|unexpected symbol",
            "type": "Syntax Error",
            "cause": "There's a syntax error in your R code.",
            "suggestions": [
                "Check for missing commas, parentheses, or quotes",
                "Make sure all brackets are properly closed",
                "Check for stray characters or typos",
                "Use <- instead of = for assignment (recommended)"
            ]
        },
    }
    
    def parse(self, error_message: str, code_context: str = "") -> ParsedError:
        """
        Parse an R error message and provide helpful context.
        
        Args:
            error_message: The raw R error message
            code_context: The code that caused the error (optional)
        
        Returns:
            ParsedError with structured information
        """
        # Try to match against known patterns
        for error_key, pattern_info in self.ERROR_PATTERNS.items():
            match = re.search(pattern_info["pattern"], error_message, re.IGNORECASE)
            if match:
                # Extract matched groups if any
                matched_value = match.group(1) if match.lastindex else ""
                
                cause = pattern_info["cause"].format(match=matched_value)
                suggestions = [s.format(match=matched_value) for s in pattern_info["suggestions"]]
                
                return ParsedError(
                    error_type=pattern_info["type"],
                    error_message=error_message.strip(),
                    line_number=self._extract_line_number(error_message),
                    function_name=self._extract_function(error_message),
                    likely_cause=cause,
                    suggestions=suggestions
                )
        
        # Generic error if no pattern matches
        return ParsedError(
            error_type="R Error",
            error_message=error_message.strip(),
            line_number=self._extract_line_number(error_message),
            function_name=self._extract_function(error_message),
            likely_cause="An error occurred in R. See the error message for details.",
            suggestions=[
                "Read the error message carefully - it often tells you the problem",
                "Check your variable names and data types",
                "Make sure all required packages are loaded",
                "Ask BioStation AI to explain this specific error"
            ]
        )
    
    def _extract_line_number(self, error: str) -> Optional[int]:
        """Extract line number from error if present"""
        match = re.search(r"line (\d+)", error, re.IGNORECASE)
        return int(match.group(1)) if match else None
    
    def _extract_function(self, error: str) -> Optional[str]:
        """Extract function name from error if present"""
        match = re.search(r"Error in (\w+(?:\.\w+)?)\s*\(", error)
        return match.group(1) if match else None
    
    def format_for_user(self, parsed: ParsedError) -> str:
        """Format parsed error for user display"""
        output = f"""## ❌ {parsed.error_type}

**Error message:**
```
{parsed.error_message}
```

**What went wrong:**
{parsed.likely_cause}

**How to fix it:**
{"".join('• ' + s + chr(10) for s in parsed.suggestions)}
"""
        return output


# Singleton instance
error_parser = RErrorParser()
