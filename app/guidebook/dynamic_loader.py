
import json
import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from .knowledge_base import STATISTICAL_CONCEPTS as STATIC_CONCEPTS

logger = logging.getLogger(__name__)

# Path to custom concepts file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CUSTOM_CONCEPTS_PATH = os.path.join(BASE_DIR, "data", "knowledge", "custom_concepts.json")
CUSTOM_TESTS_PATH = os.path.join(BASE_DIR, "data", "knowledge", "custom_tests.json")

# Category detection keywords
CATEGORY_KEYWORDS = {
    'non-parametric': ['non-parametric', 'nonparametric', 'rank', 'ordinal', 'mann-whitney',
                       'wilcoxon', 'kruskal', 'friedman', 'sign test', 'median test'],
    'parametric': ['parametric', 't-test', 'ttest', 'anova', 'normal', 'gaussian', 'f-test'],
    'regression': ['regression', 'predict', 'model', 'linear', 'logistic', 'glm', 'lm('],
    'correlation': ['correlation', 'pearson', 'spearman', 'kendall', 'relationship', 'association'],
    'categorical': ['categorical', 'chi-squared', 'chi-square', 'fisher', 'contingency', 'mcnemar'],
    'survival': ['survival', 'time-to-event', 'hazard', 'kaplan', 'cox', 'censored'],
    'descriptive': ['descriptive', 'summary', 'mean', 'median', 'variance', 'standard deviation'],
}

# Valid placeholders for R templates
VALID_PLACEHOLDERS = [
    'data', 'data_loading', 'package_helper',
    'y_var', 'y_var_name', 'y_var_clean',
    'x_var', 'x_var_name', 'x_var_clean',
    'group_var', 'group_var_name', 'group_var_clean',
    'subject_var', 'subject_var_clean',
    'var1', 'var2', 'before_var', 'after_var',
    'predictors', 'random_var', 'fixed_effects',
    'smooth_var', 'time_var', 'event_var',
    'mu', 'family', 'correlation_method'
]

def load_knowledge_base() -> Dict:
    """
    Load the full knowledge base by merging static concepts with user-defined ones.
    User-defined concepts take precedence (override static ones).
    """
    # Start with static concepts
    knowledge_base = STATIC_CONCEPTS.copy()
    
    # Load custom concepts if file exists
    if os.path.exists(CUSTOM_CONCEPTS_PATH):
        try:
            with open(CUSTOM_CONCEPTS_PATH, 'r', encoding='utf-8') as f:
                custom_concepts = json.load(f)
                
            # Merge custom concepts
            # Using update() means custom concepts with same ID will overwrite static ones
            knowledge_base.update(custom_concepts)
            logger.info(f"Loaded {len(custom_concepts)} custom concepts")
        except Exception as e:
            logger.error(f"Failed to load custom concepts: {e}")
    
    return knowledge_base

def save_custom_concept(concept_id: str, title: str, content: str, keywords: list):
    """Save a new concept or update an existing one"""
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(CUSTOM_CONCEPTS_PATH), exist_ok=True)
    
    # Load existing
    custom_concepts = {}
    if os.path.exists(CUSTOM_CONCEPTS_PATH):
        try:
            with open(CUSTOM_CONCEPTS_PATH, 'r', encoding='utf-8') as f:
                custom_concepts = json.load(f)
        except:
            custom_concepts = {}
            
    # Update/Add
    from datetime import datetime
    custom_concepts[concept_id] = {
        "title": title,
        "content": content,
        "keywords": keywords,
        "added_at": datetime.now().isoformat(),
        "source": "user_teach_mode"
    }
    
    # Save back
    with open(CUSTOM_CONCEPTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(custom_concepts, f, indent=2)

    logger.info(f"Saved custom concept: {concept_id}")
    return True


# ============ CUSTOM STATISTICAL TESTS ============

def auto_categorize_test(keywords: List[str], explanation: str, purpose: str) -> str:
    """
    Auto-detect the category of a statistical test based on keywords and content.
    Returns one of: parametric, non-parametric, regression, correlation, categorical, survival, other
    """
    # Combine all text for searching
    all_text = ' '.join(keywords + [explanation, purpose]).lower()

    # Score each category
    scores = {}
    for category, category_keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in category_keywords if kw in all_text)
        if score > 0:
            scores[category] = score

    # Return category with highest score, or 'other' if no matches
    if scores:
        return max(scores, key=scores.get)
    return 'other'


def extract_packages(r_code: str) -> List[str]:
    """
    Extract required R packages from R code template.
    Looks for library() and ensure_package() calls.
    """
    packages = set()

    # Match library(package) or library("package")
    library_pattern = r'library\s*\(\s*["\']?(\w+)["\']?\s*\)'
    for match in re.finditer(library_pattern, r_code):
        packages.add(match.group(1))

    # Match ensure_package("package")
    ensure_pattern = r'ensure_package\s*\(\s*["\'](\w+)["\']\s*\)'
    for match in re.finditer(ensure_pattern, r_code):
        packages.add(match.group(1))

    # Match require(package)
    require_pattern = r'require\s*\(\s*["\']?(\w+)["\']?\s*\)'
    for match in re.finditer(require_pattern, r_code):
        packages.add(match.group(1))

    return list(packages)


def validate_r_syntax(r_code: str) -> Tuple[bool, Optional[str]]:
    """
    Basic R syntax validation.
    Returns (is_valid, error_message).
    """
    if not r_code or not r_code.strip():
        return False, "R code template cannot be empty"

    # Check for unmatched parentheses
    open_parens = r_code.count('(')
    close_parens = r_code.count(')')
    if open_parens != close_parens:
        return False, f"Unmatched parentheses: {open_parens} '(' vs {close_parens} ')'"

    # Check for unmatched brackets
    open_brackets = r_code.count('[')
    close_brackets = r_code.count(']')
    if open_brackets != close_brackets:
        return False, f"Unmatched brackets: {open_brackets} '[' vs {close_brackets} ']'"

    # Check for unmatched curly braces (accounting for {{ }} escapes)
    # In Python format strings, {{ and }} are escaped braces
    # Remove escaped braces first for counting
    code_for_braces = r_code.replace('{{', '').replace('}}', '')
    open_braces = code_for_braces.count('{')
    close_braces = code_for_braces.count('}')
    if open_braces != close_braces:
        return False, f"Unmatched curly braces: {open_braces} '{{' vs {close_braces} '}}'"

    # Check for valid placeholders
    placeholder_pattern = r'\{(\w+)\}'
    for match in re.finditer(placeholder_pattern, r_code):
        placeholder = match.group(1)
        if placeholder not in VALID_PLACEHOLDERS:
            return False, f"Invalid placeholder '{{{placeholder}}}'. Valid placeholders: {', '.join(VALID_PLACEHOLDERS[:10])}..."

    # Check for common R syntax errors
    if '<-' not in r_code and '=' not in r_code:
        logger.warning("R code has no assignments - this may be intentional")

    return True, None


def save_custom_test(
    test_id: str,
    name: str,
    keywords: List[str],
    purpose: str,
    explanation: str,
    assumptions: str,
    r_template: str
) -> Tuple[bool, Optional[str]]:
    """
    Save a custom statistical test with R template.
    Returns (success, error_message).
    """
    # Validate R syntax first
    is_valid, error = validate_r_syntax(r_template)
    if not is_valid:
        return False, f"R code validation failed: {error}"

    # Ensure directory exists
    os.makedirs(os.path.dirname(CUSTOM_TESTS_PATH), exist_ok=True)

    # Load existing custom tests
    custom_tests = {}
    if os.path.exists(CUSTOM_TESTS_PATH):
        try:
            with open(CUSTOM_TESTS_PATH, 'r', encoding='utf-8') as f:
                custom_tests = json.load(f)
        except Exception:
            custom_tests = {}

    # Auto-categorize the test
    category = auto_categorize_test(keywords, explanation, purpose)

    # Extract required packages
    packages = extract_packages(r_template)

    # Ensure package_helper is at the start if not present
    if '{package_helper}' not in r_template:
        r_template = '{package_helper}\n' + r_template

    # Ensure data_loading is present
    if '{data_loading}' not in r_template:
        # Add after package_helper
        r_template = r_template.replace(
            '{package_helper}\n',
            '{package_helper}\n\n# Load data\n{data_loading}\n\n'
        )

    # Create test entry
    from datetime import datetime
    custom_tests[test_id] = {
        "id": test_id,
        "name": name,
        "category": category,
        "keywords": keywords,
        "purpose": purpose,
        "explanation": explanation,
        "assumptions": assumptions,
        "r_template": r_template,
        "r_packages": packages,
        "added_at": datetime.now().isoformat(),
        "source": "user_teach_mode"
    }

    # Save to file
    try:
        with open(CUSTOM_TESTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(custom_tests, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved custom test: {test_id} (category: {category})")
        return True, None
    except Exception as e:
        logger.error(f"Failed to save custom test: {e}")
        return False, str(e)


def load_custom_tests() -> Dict:
    """
    Load all custom statistical tests.
    Returns dict of test_id -> test_data.
    """
    if not os.path.exists(CUSTOM_TESTS_PATH):
        return {}

    try:
        with open(CUSTOM_TESTS_PATH, 'r', encoding='utf-8') as f:
            custom_tests = json.load(f)
        logger.info(f"Loaded {len(custom_tests)} custom tests")
        return custom_tests
    except Exception as e:
        logger.error(f"Failed to load custom tests: {e}")
        return {}


def get_custom_test(test_id: str) -> Optional[Dict]:
    """Get a specific custom test by ID."""
    custom_tests = load_custom_tests()
    return custom_tests.get(test_id)


def get_custom_test_keywords_mapping() -> Dict[str, str]:
    """
    Get keyword -> test_id mapping for all custom tests.
    Used to merge into TEST_MAPPING in base.py.
    """
    custom_tests = load_custom_tests()
    mapping = {}

    for test_id, test_data in custom_tests.items():
        for keyword in test_data.get('keywords', []):
            mapping[keyword.lower()] = test_id
        # Also add the test name itself
        mapping[test_data.get('name', '').lower()] = test_id

    return mapping


def delete_custom_test(test_id: str) -> Tuple[bool, Optional[str]]:
    """
    Delete a custom statistical test.
    Returns (success, error_message).
    """
    if not os.path.exists(CUSTOM_TESTS_PATH):
        return False, "No custom tests file found"

    try:
        with open(CUSTOM_TESTS_PATH, 'r', encoding='utf-8') as f:
            custom_tests = json.load(f)
    except Exception as e:
        return False, f"Failed to load custom tests: {e}"

    if test_id not in custom_tests:
        return False, f"Test '{test_id}' not found"

    # Get test name for logging
    test_name = custom_tests[test_id].get('name', test_id)

    # Delete the test
    del custom_tests[test_id]

    # Save back to file
    try:
        with open(CUSTOM_TESTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(custom_tests, f, indent=2, ensure_ascii=False)
        logger.info(f"Deleted custom test: {test_name} ({test_id})")
        return True, None
    except Exception as e:
        logger.error(f"Failed to delete custom test: {e}")
        return False, str(e)
