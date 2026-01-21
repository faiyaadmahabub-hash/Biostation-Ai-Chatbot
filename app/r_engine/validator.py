"""
Data Validator - Validate and preprocess uploaded datasets
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation"""
    valid: bool
    issues: List[str]
    warnings: List[str]
    summary: Dict
    cleaned_data: Optional[pd.DataFrame] = None


class DataValidator:
    """Validate and preprocess datasets for statistical analysis"""
    
    def __init__(self):
        self.max_rows = 100000
        self.max_cols = 500
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate a DataFrame for statistical analysis.
        
        Args:
            df: Pandas DataFrame to validate
        
        Returns:
            ValidationResult with issues, warnings, and cleaned data
        """
        issues = []
        warnings = []
        summary = {}
        
        # Basic info
        summary['rows'] = len(df)
        summary['columns'] = len(df.columns)
        summary['column_names'] = list(df.columns)
        
        # Check size limits
        if len(df) > self.max_rows:
            issues.append(f"Dataset too large: {len(df)} rows (max: {self.max_rows})")
        
        if len(df.columns) > self.max_cols:
            issues.append(f"Too many columns: {len(df.columns)} (max: {self.max_cols})")
        
        # Check for empty dataframe
        if len(df) == 0:
            issues.append("Dataset is empty (0 rows)")
            return ValidationResult(False, issues, warnings, summary)
        
        # Check for duplicate column names
        if len(df.columns) != len(set(df.columns)):
            duplicates = [col for col in df.columns if list(df.columns).count(col) > 1]
            issues.append(f"Duplicate column names found: {set(duplicates)}")
        
        # Analyze each column
        column_info = []
        for col in df.columns:
            col_info = self._analyze_column(df[col])
            column_info.append(col_info)
            
            # Add warnings for problematic columns
            if col_info['missing_pct'] > 50:
                warnings.append(f"Column '{col}' is >50% missing values")
            
            if col_info['dtype'] == 'object' and col_info['unique_count'] == len(df):
                warnings.append(f"Column '{col}' has all unique values (likely an ID column)")
        
        summary['column_info'] = column_info
        
        # Check for overall data quality
        total_missing = df.isnull().sum().sum()
        total_cells = df.size
        missing_pct = (total_missing / total_cells) * 100 if total_cells > 0 else 0
        summary['missing_percentage'] = round(missing_pct, 2)
        
        if missing_pct > 20:
            warnings.append(f"High proportion of missing values: {missing_pct:.1f}%")
        
        return ValidationResult(
            valid=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            summary=summary,
            cleaned_data=df
        )
    
    def _analyze_column(self, series: pd.Series) -> Dict:
        """Analyze a single column"""
        info = {
            'name': series.name,
            'dtype': str(series.dtype),
            'missing_count': int(series.isnull().sum()),
            'missing_pct': round((series.isnull().sum() / len(series)) * 100, 2),
            'unique_count': int(series.nunique())
        }
        
        # Determine variable type
        if pd.api.types.is_numeric_dtype(series):
            info['var_type'] = 'numeric'
            non_null = series.dropna()
            if len(non_null) > 0:
                info['min'] = float(non_null.min())
                info['max'] = float(non_null.max())
                info['mean'] = float(non_null.mean())
                info['std'] = float(non_null.std())
        elif pd.api.types.is_categorical_dtype(series) or series.nunique() < 20:
            info['var_type'] = 'categorical'
            info['categories'] = series.value_counts().head(10).to_dict()
        else:
            info['var_type'] = 'text'
        
        return info
    
    def preprocess(
        self, 
        df: pd.DataFrame,
        remove_duplicates: bool = True,
        handle_missing: str = 'keep',  # 'keep', 'drop', 'mean', 'median'
        standardize_names: bool = True
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Preprocess a DataFrame.
        
        Args:
            df: Input DataFrame
            remove_duplicates: Remove duplicate rows
            handle_missing: How to handle missing values
            standardize_names: Clean up column names
        
        Returns:
            Tuple of (processed DataFrame, list of changes made)
        """
        changes = []
        result = df.copy()
        
        # Standardize column names
        if standardize_names:
            old_names = list(result.columns)
            new_names = [self._clean_column_name(name) for name in old_names]
            
            # Handle duplicates by adding suffix
            seen = {}
            final_names = []
            for name in new_names:
                if name in seen:
                    seen[name] += 1
                    final_names.append(f"{name}_{seen[name]}")
                else:
                    seen[name] = 0
                    final_names.append(name)
            
            result.columns = final_names
            
            renamed = [(old, new) for old, new in zip(old_names, final_names) if old != new]
            if renamed:
                changes.append(f"Renamed {len(renamed)} columns to valid R names")
        
        # Remove duplicates
        if remove_duplicates:
            original_len = len(result)
            result = result.drop_duplicates()
            removed = original_len - len(result)
            if removed > 0:
                changes.append(f"Removed {removed} duplicate rows")
        
        # Handle missing values
        if handle_missing == 'drop':
            original_len = len(result)
            result = result.dropna()
            removed = original_len - len(result)
            if removed > 0:
                changes.append(f"Removed {removed} rows with missing values")
        
        elif handle_missing in ('mean', 'median'):
            numeric_cols = result.select_dtypes(include=[np.number]).columns
            filled_count = 0
            
            for col in numeric_cols:
                missing = result[col].isnull().sum()
                if missing > 0:
                    if handle_missing == 'mean':
                        result[col].fillna(result[col].mean(), inplace=True)
                    else:
                        result[col].fillna(result[col].median(), inplace=True)
                    filled_count += missing
            
            if filled_count > 0:
                changes.append(f"Filled {filled_count} missing values with {handle_missing}")
        
        return result, changes
    
    def _clean_column_name(self, name: str) -> str:
        """Clean column name for R compatibility"""
        import re
        
        # Convert to string
        name = str(name)
        
        # Replace spaces and special chars with underscore
        name = re.sub(r'[^a-zA-Z0-9_.]', '_', name)
        
        # Remove leading numbers
        if name and name[0].isdigit():
            name = 'X' + name
        
        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove trailing underscore
        name = name.rstrip('_')
        
        return name if name else 'column'
    
    def suggest_tests(self, df: pd.DataFrame, outcome_col: str = None, group_col: str = None) -> List[Dict]:
        """
        Suggest appropriate statistical tests based on data characteristics.
        
        Args:
            df: The dataset
            outcome_col: Name of outcome/dependent variable
            group_col: Name of grouping variable (if any)
        
        Returns:
            List of suggested tests with rationale
        """
        suggestions = []
        
        if outcome_col and outcome_col not in df.columns:
            return [{"error": f"Column '{outcome_col}' not found"}]
        
        if group_col and group_col not in df.columns:
            return [{"error": f"Column '{group_col}' not found"}]
        
        outcome = df[outcome_col] if outcome_col else None
        group = df[group_col] if group_col else None
        
        # Determine outcome type
        if outcome is not None:
            is_numeric_outcome = pd.api.types.is_numeric_dtype(outcome)
        else:
            is_numeric_outcome = None
        
        # If we have a grouping variable
        if group is not None:
            n_groups = group.nunique()
            
            if is_numeric_outcome:
                if n_groups == 2:
                    suggestions.append({
                        'test': 'unpaired_ttest',
                        'name': 'Independent T-Test',
                        'reason': f"Comparing numeric outcome across 2 groups ({n_groups} unique values in {group_col})"
                    })
                    suggestions.append({
                        'test': 'mann_whitney',
                        'name': 'Mann-Whitney U Test',
                        'reason': "Non-parametric alternative if normality is violated"
                    })
                elif n_groups > 2:
                    suggestions.append({
                        'test': 'anova',
                        'name': 'One-Way ANOVA',
                        'reason': f"Comparing numeric outcome across {n_groups} groups"
                    })
                    suggestions.append({
                        'test': 'kruskal_wallis',
                        'name': 'Kruskal-Wallis Test',
                        'reason': "Non-parametric alternative if normality is violated"
                    })
            else:
                # Categorical outcome
                suggestions.append({
                    'test': 'chi_squared',
                    'name': 'Chi-Squared Test',
                    'reason': "Testing association between two categorical variables"
                })
        
        # Correlation suggestions
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            suggestions.append({
                'test': 'pearson_correlation',
                'name': 'Pearson Correlation',
                'reason': f"You have {len(numeric_cols)} numeric columns that could be correlated"
            })
        
        return suggestions


# Singleton instance
data_validator = DataValidator()
