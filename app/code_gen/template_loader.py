"""
R Template Loader - Load and fill R code templates from files
Supports both built-in templates and user-defined custom templates.
"""

from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TemplateLoader:
    """
    Loads R code templates from .r files and fills placeholders.
    Templates use {variable_name} syntax for substitution.
    """

    # Mapping of test IDs to template file paths
    TEMPLATE_MAP = {
        # T-tests
        'one_sample_ttest': 'ttests/one_sample_ttest.r',
        'unpaired_ttest': 'ttests/unpaired_ttest.r',
        'paired_ttest': 'ttests/paired_ttest.r',

        # ANOVA
        'anova': 'anova/one_way_anova.r',
        'two_way_anova': 'anova/two_way_anova.r',

        # Non-parametric
        'mann_whitney': 'nonparametric/mann_whitney.r',
        'wilcoxon_signed_rank': 'nonparametric/wilcoxon_signed_rank.r',
        'kruskal_wallis': 'nonparametric/kruskal_wallis.r',

        # Correlation
        'pearson_correlation': 'correlation/pearson_correlation.r',
        'spearman_correlation': 'correlation/spearman_correlation.r',
        'correlation_matrix': 'correlation/correlation_matrix.r',

        # Categorical
        'chi_squared': 'categorical/chi_squared.r',
        'fisher_exact': 'categorical/fisher_exact.r',

        # Regression
        'linear_regression': 'regression/linear_regression.r',
        'glm': 'regression/glm.r',
        'glmm': 'regression/glmm.r',
        'gam': 'regression/gam.r',

        # Survival
        'kaplan_meier': 'survival/kaplan_meier.r',
        'cox_regression': 'survival/cox_regression.r',

        # Diagnostics
        'normality_test': 'diagnostics/normality_test.r',
        'descriptive': 'diagnostics/descriptive.r',
    }

    def __init__(self):
        """Initialize template loader"""
        self.template_dir = Path(__file__).parent / 'templates'
        self.package_helper = self._load_package_helper()
        self._custom_tests_cache = None  # Lazy-loaded cache

    def _load_package_helper(self) -> str:
        """Load the shared package installer helper"""
        helper_path = self.template_dir / 'helpers' / 'package_installer.r'
        if helper_path.exists():
            return helper_path.read_text(encoding='utf-8')
        return ""

    def _get_custom_tests(self) -> Dict:
        """
        Load custom tests from dynamic_loader.
        Always reloads from JSON to pick up user modifications.
        """
        try:
            from app.guidebook.dynamic_loader import load_custom_tests
            return load_custom_tests()
        except ImportError:
            logger.warning("Could not import dynamic_loader for custom tests")
            return {}

    def refresh_custom_tests(self):
        """Force refresh of custom tests cache."""
        self._custom_tests_cache = None

    def is_custom_test(self, test_id: str) -> bool:
        """Check if a test ID refers to a custom (user-taught) test."""
        return test_id in self._get_custom_tests()

    def get_custom_template(self, test_id: str) -> Optional[str]:
        """
        Get R template for a custom test.
        Returns None if test doesn't exist.
        """
        custom_tests = self._get_custom_tests()
        if test_id in custom_tests:
            return custom_tests[test_id].get('r_template')
        return None

    def template_exists(self, test_id: str) -> bool:
        """Check if template exists for given test ID (built-in or custom)"""
        # Check custom tests first
        if self.is_custom_test(test_id):
            return True

        # Check built-in templates
        if test_id not in self.TEMPLATE_MAP:
            return False

        template_path = self.template_dir / self.TEMPLATE_MAP[test_id]
        return template_path.exists()

    def load_template(self, test_id: str) -> str:
        """
        Load R template from file or custom tests.

        Args:
            test_id: ID of the statistical test

        Returns:
            Template string with {placeholders}

        Raises:
            FileNotFoundError: If template file doesn't exist
            KeyError: If test_id not found in TEMPLATE_MAP or custom tests
        """
        # Check custom tests first
        custom_template = self.get_custom_template(test_id)
        if custom_template:
            logger.info(f"Loading custom template for: {test_id}")
            return custom_template

        # Fall back to built-in templates
        if test_id not in self.TEMPLATE_MAP:
            raise KeyError(f"No template defined for test_id: {test_id}")

        template_path = self.template_dir / self.TEMPLATE_MAP[test_id]

        if not template_path.exists():
            raise FileNotFoundError(
                f"Template file not found: {template_path}\n"
                f"Expected: {self.template_dir / self.TEMPLATE_MAP[test_id]}"
            )

        return template_path.read_text(encoding='utf-8')

    def fill_template(
        self,
        template: str,
        variables: Dict[str, str],
        data_source: str = "your_data.csv"
    ) -> str:
        """
        Fill template placeholders with actual values.

        Args:
            template: R template string with {placeholders}
            variables: Dict mapping placeholder names to values
            data_source: Path to data file or data frame name

        Returns:
            Filled R code ready to execute
        """
        # Create data loading code
        if data_source.endswith('.csv'):
            data_loading = f'data <- read.csv("{data_source}")'
        elif data_source.endswith(('.xlsx', '.xls')):
            data_loading = f'library(readxl)\ndata <- read_excel("{data_source}")'
        else:
            data_loading = f'# data <- {data_source}  # Your data frame'

        # Helper to clean variable names (remove data$ prefix)
        def clean_var(v):
            return v.replace("data$", "").replace('"', '')

        # Build replacement dict with defaults
        replacements = {
            'package_helper': self.package_helper,
            'data_loading': data_loading,
            'data': 'data',
            'y_var': variables.get('y', 'data$outcome'),
            'y_var_name': variables.get('y_name', 'Outcome Variable'),
            'y_var_clean': clean_var(variables.get('y', 'outcome')),
            'x_var': variables.get('x', 'data$predictor'),
            'x_var_name': variables.get('x_name', 'Predictor Variable'),
            'x_var_clean': clean_var(variables.get('x', 'predictor')),
            'group_var': variables.get('group', 'data$group'),
            'group_var_name': variables.get('group_name', 'Group'),
            'group_var_clean': clean_var(variables.get('group', 'group')),
            'before_var': variables.get('before', 'data$before'),
            'after_var': variables.get('after', 'data$after'),
            'var1': variables.get('var1', 'data$variable1'),
            'var2': variables.get('var2', 'data$variable2'),
            'predictors': variables.get('predictors', 'predictor1 + predictor2'),
            # GLMM parameters
            'random_var': variables.get('random', 'data$subject_id'),
            'subject_var': variables.get('subject', 'subject_id'),
            'subject_var_clean': clean_var(variables.get('subject', 'subject_id')),
            'fixed_effects': variables.get('fixed_effects', 'predictor1 + predictor2'),
            # GAM parameters
            'smooth_var': variables.get('smooth', 'data$predictor'),
            # Survival analysis parameters
            'time_var': variables.get('time', 'data$time'),
            'event_var': variables.get('event', 'data$status'),
            # General parameters
            'mu': variables.get('mu', '0'),
            'family': variables.get('family', 'binomial'),
            # Correlation matrix parameters
            'correlation_method': variables.get('correlation_method', 'pearson'),
        }

        # Add any custom variables
        replacements.update(variables)

        # Fill template
        try:
            filled_code = template.format(**replacements)
            return filled_code
        except KeyError as e:
            raise KeyError(f"Missing required variable in template: {e}")

    def generate_code(
        self,
        test_id: str,
        data_source: str = "your_data.csv",
        variables: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Load template and generate filled R code in one step.

        Args:
            test_id: ID of the statistical test
            data_source: Path to data file
            variables: Variable mappings for template

        Returns:
            Complete R code ready to execute
        """
        template = self.load_template(test_id)
        variables = variables or {}
        return self.fill_template(template, variables, data_source)


# Singleton instance
_template_loader = None


def get_template_loader() -> TemplateLoader:
    """Get or create template loader singleton"""
    global _template_loader
    if _template_loader is None:
        _template_loader = TemplateLoader()
    return _template_loader


def refresh_template_loader():
    """Refresh template loader to pick up new custom tests."""
    loader = get_template_loader()
    loader.refresh_custom_tests()
