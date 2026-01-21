"""
Code Corrector - Automatically suggest and apply fixes for R code errors
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CorrectionSuggestion:
    """A suggested code correction"""
    original_line: str
    corrected_line: str
    explanation: str
    confidence: float  # 0.0 to 1.0
    line_number: Optional[int] = None


@dataclass
class CorrectionResult:
    """Result of code correction analysis"""
    has_errors: bool
    suggestions: List[CorrectionSuggestion]
    corrected_code: Optional[str]
    explanation: str


class CodeCorrector:
    """
    Analyze R code errors and suggest corrections.
    """
    
    # Common error patterns and their fixes
    CORRECTION_PATTERNS = [
        # Missing quotes around string
        {
            'error_pattern': r"object '(\w+)' not found",
            'code_pattern': r'(\w+)\s*=\s*{match}([^"\'])',
            'fix': lambda m, match: f'{m.group(1)} = "{match}"',
            'explanation': "String values should be quoted"
        },
        # Wrong assignment operator
        {
            'error_pattern': r"unexpected '='",
            'code_pattern': r'(\w+)\s*=\s*(\w+)',
            'fix': lambda m: f'{m.group(1)} <- {m.group(2)}',
            'explanation': "Use <- for assignment in R (preferred over =)"
        },
        # Missing library
        {
            'error_pattern': r"there is no package called '(\w+)'",
            'suggestion': 'install.packages("{match}")\nlibrary({match})',
            'explanation': "Package needs to be installed first"
        },
        # Function not found (common typos)
        {
            'error_pattern': r"could not find function \"(\w+)\"",
            'typo_fixes': {
                'read_csv': 'read.csv',
                'readcsv': 'read.csv',
                'ttest': 't.test',
                'wilcoxtest': 'wilcox.test',
                'chisqtest': 'chisq.test',
                'summarize': 'summary',
                'lenght': 'length',
                'pritn': 'print',
                'retrun': 'return'
            },
            'explanation': "Function name may be misspelled"
        },
        # Missing comma
        {
            'error_pattern': r"unexpected symbol",
            'code_pattern': r'(\w+)\s+(\w+)\s*[=<-]',
            'fix': lambda m: f'{m.group(1)}, {m.group(2)} =',
            'explanation': "Arguments should be separated by commas"
        },
        # Unclosed parenthesis
        {
            'error_pattern': r"unexpected end of input|unexpected '\)'",
            'check': 'parentheses',
            'explanation': "Check for matching parentheses, brackets, or braces"
        },
        # Unclosed string
        {
            'error_pattern': r"unexpected end of input|EOF within quoted string",
            'check': 'quotes',
            'explanation': "Check for unclosed quotes (\" or ')"
        },
    ]
    
    # Common fixes for specific function errors
    FUNCTION_FIXES = {
        't.test': {
            'common_errors': [
                ("non-numeric argument", "Ensure the data column is numeric. Use as.numeric() if needed."),
                ("data are essentially constant", "Your data has no variance. Check for errors in data."),
                ("not enough 'x' observations", "Need at least 2 data points per group."),
            ],
            'template': 't.test({x}, {y}, paired = FALSE, var.equal = FALSE)'
        },
        'aov': {
            'common_errors': [
                ("singular matrix", "Check for constant columns or perfect multicollinearity."),
                ("factor", "The grouping variable should be a factor. Use as.factor()."),
            ],
            'template': 'aov({formula}, data = {data})'
        },
        'cor.test': {
            'common_errors': [
                ("not enough finite observations", "Too many NA values. Use na.rm = TRUE."),
                ("'x' and 'y' must have the same length", "Vectors must be same length."),
            ],
            'template': 'cor.test({x}, {y}, method = "pearson")'
        },
        'lm': {
            'common_errors': [
                ("NA/NaN/Inf", "Data contains invalid values. Clean data first."),
                ("singular fit", "Perfect multicollinearity detected. Remove redundant predictors."),
            ],
            'template': 'lm({formula}, data = {data})'
        }
    }
    
    def analyze_and_correct(self, code: str, error_message: str) -> CorrectionResult:
        """
        Analyze R code and error message, suggest corrections.
        
        Args:
            code: The R code that produced the error
            error_message: The error message from R
        
        Returns:
            CorrectionResult with suggestions and corrected code
        """
        suggestions = []
        corrected_code = code
        explanation_parts = []
        
        # Check each correction pattern
        for pattern in self.CORRECTION_PATTERNS:
            error_match = re.search(pattern['error_pattern'], error_message, re.IGNORECASE)
            if error_match:
                matched_value = error_match.group(1) if error_match.lastindex else ""
                
                # Handle typo fixes
                if 'typo_fixes' in pattern:
                    if matched_value.lower() in pattern['typo_fixes']:
                        correct_func = pattern['typo_fixes'][matched_value.lower()]
                        suggestions.append(CorrectionSuggestion(
                            original_line=matched_value,
                            corrected_line=correct_func,
                            explanation=f"'{matched_value}' → '{correct_func}': {pattern['explanation']}",
                            confidence=0.9
                        ))
                        corrected_code = corrected_code.replace(matched_value, correct_func)
                
                # Handle suggestion-only patterns
                if 'suggestion' in pattern:
                    suggestion_code = pattern['suggestion'].format(match=matched_value)
                    suggestions.append(CorrectionSuggestion(
                        original_line="",
                        corrected_line=suggestion_code,
                        explanation=pattern['explanation'],
                        confidence=0.8
                    ))
                    explanation_parts.append(pattern['explanation'])
                
                # Handle check patterns (structural issues)
                if 'check' in pattern:
                    if pattern['check'] == 'parentheses':
                        fix = self._fix_parentheses(code)
                        if fix != code:
                            suggestions.append(CorrectionSuggestion(
                                original_line=code,
                                corrected_line=fix,
                                explanation="Fixed unbalanced parentheses",
                                confidence=0.7
                            ))
                            corrected_code = fix
                    
                    elif pattern['check'] == 'quotes':
                        fix = self._fix_quotes(code)
                        if fix != code:
                            suggestions.append(CorrectionSuggestion(
                                original_line=code,
                                corrected_line=fix,
                                explanation="Fixed unclosed string quotes",
                                confidence=0.7
                            ))
                            corrected_code = fix
                    
                    explanation_parts.append(pattern['explanation'])
        
        # Check for function-specific errors
        for func_name, func_info in self.FUNCTION_FIXES.items():
            if func_name in code:
                for error_pattern, error_fix in func_info['common_errors']:
                    if error_pattern.lower() in error_message.lower():
                        suggestions.append(CorrectionSuggestion(
                            original_line="",
                            corrected_line=f"# Tip: {error_fix}\n# Template: {func_info['template']}",
                            explanation=error_fix,
                            confidence=0.85
                        ))
                        explanation_parts.append(error_fix)
        
        # Generate overall explanation
        if suggestions:
            explanation = "**Suggested fixes:**\n" + "\n".join(
                f"• {s.explanation}" for s in suggestions
            )
        else:
            explanation = "Could not automatically determine a fix. Please review the error message."
        
        return CorrectionResult(
            has_errors=True,
            suggestions=suggestions,
            corrected_code=corrected_code if corrected_code != code else None,
            explanation=explanation
        )
    
    def _fix_parentheses(self, code: str) -> str:
        """Attempt to fix unbalanced parentheses"""
        # Count parentheses
        open_count = code.count('(')
        close_count = code.count(')')
        
        if open_count > close_count:
            # Add missing closing parentheses
            code = code + ')' * (open_count - close_count)
        elif close_count > open_count:
            # Remove extra closing parentheses from end
            while code.endswith(')') and code.count(')') > code.count('('):
                code = code[:-1]
        
        # Same for brackets
        open_bracket = code.count('[')
        close_bracket = code.count(']')
        if open_bracket > close_bracket:
            code = code + ']' * (open_bracket - close_bracket)
        
        # Same for braces
        open_brace = code.count('{')
        close_brace = code.count('}')
        if open_brace > close_brace:
            code = code + '}' * (open_brace - close_brace)
        
        return code
    
    def _fix_quotes(self, code: str) -> str:
        """Attempt to fix unclosed quotes"""
        # Count quotes
        double_quotes = code.count('"')
        single_quotes = code.count("'")
        
        if double_quotes % 2 != 0:
            # Add missing double quote at end
            code = code + '"'
        
        if single_quotes % 2 != 0:
            # Add missing single quote at end
            code = code + "'"
        
        return code
    
    def get_fix_template(self, test_id: str, error_type: str) -> Optional[str]:
        """Get a fix template for a specific test and error type"""
        from app.advisor import get_test_info
        
        test_info = get_test_info(test_id)
        if not test_info:
            return None
        
        templates = {
            ('unpaired_ttest', 'non-numeric'): '''
# Fix: Ensure data is numeric
data${var} <- as.numeric(data${var})
# Then run the test
t.test({var} ~ group, data = data)
''',
            ('anova', 'factor'): '''
# Fix: Convert grouping variable to factor
data$group <- as.factor(data$group)
# Then run ANOVA
model <- aov(outcome ~ group, data = data)
summary(model)
''',
            ('pearson_correlation', 'na'): '''
# Fix: Remove NA values before correlation
complete_data <- na.omit(data[, c("x", "y")])
cor.test(complete_data$x, complete_data$y)
''',
        }
        
        return templates.get((test_id, error_type))
    
    def format_correction_response(self, result: CorrectionResult) -> str:
        """Format correction result for chat display"""
        if not result.suggestions:
            return f"""## 🔧 Code Analysis

I couldn't automatically fix this error, but here are some things to check:

{result.explanation}

**Need more help?** Paste your full code and I'll take a closer look."""
        
        response = "## 🔧 Code Corrections\n\n"
        
        for i, suggestion in enumerate(result.suggestions, 1):
            response += f"### Fix {i}: {suggestion.explanation}\n"
            
            if suggestion.original_line and suggestion.corrected_line:
                response += f"```diff\n- {suggestion.original_line}\n+ {suggestion.corrected_line}\n```\n"
            elif suggestion.corrected_line:
                response += f"```r\n{suggestion.corrected_line}\n```\n"
            
            response += f"*Confidence: {suggestion.confidence:.0%}*\n\n"
        
        if result.corrected_code:
            response += "### Corrected Code:\n"
            response += f"```r\n{result.corrected_code}\n```\n"
        
        return response


# Singleton instance  
code_corrector = CodeCorrector()
