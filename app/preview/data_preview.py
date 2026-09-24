"""
Data Preview Generator - Generate comprehensive dataset previews

This module provides functionality to:
1. Show first N rows of uploaded dataset
2. Display column names and inferred data types
3. Show basic stats (mean, median, min, max) for numeric columns
4. Show unique values for categorical columns (if <10 unique)
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class DataPreviewGenerator:
    """Generate comprehensive previews for uploaded datasets"""

    DEFAULT_PREVIEW_ROWS = 10
    MAX_UNIQUE_VALUES_DISPLAY = 10

    def __init__(self, df: pd.DataFrame):
        """
        Initialize with a pandas DataFrame

        Args:
            df: pandas DataFrame to generate preview for
        """
        self.df = df
        self._column_info: Optional[List[Dict]] = None

    @classmethod
    def from_file(cls, filepath: str) -> 'DataPreviewGenerator':
        """
        Create DataPreviewGenerator from a file path

        Args:
            filepath: Path to CSV or Excel file

        Returns:
            DataPreviewGenerator instance
        """
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filepath.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            # Default to CSV
            df = pd.read_csv(filepath)
        return cls(df)

    def generate_preview(self, n_rows: int = None) -> Dict[str, Any]:
        """
        Generate a complete dataset preview

        Args:
            n_rows: Number of rows to include (default: 10)

        Returns:
            Dictionary containing preview data
        """
        n_rows = n_rows or self.DEFAULT_PREVIEW_ROWS

        try:
            preview = {
                'success': True,
                'shape': {
                    'rows': len(self.df),
                    'columns': len(self.df.columns)
                },
                'columns': self._get_column_info(),
                'head': self._get_head_data(n_rows),
                'summary': self._get_summary_stats(),
                'missing_values': self._get_missing_info()
            }
            return preview
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_column_info(self) -> List[Dict[str, Any]]:
        """Get detailed information about each column"""
        if self._column_info is not None:
            return self._column_info

        columns = []
        for col in self.df.columns:
            col_data = self.df[col]
            dtype = str(col_data.dtype)

            # Determine column type category
            if pd.api.types.is_numeric_dtype(col_data):
                type_category = 'numeric'
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                type_category = 'datetime'
            elif pd.api.types.is_bool_dtype(col_data):
                type_category = 'boolean'
            else:
                type_category = 'categorical'

            col_info = {
                'name': col,
                'dtype': dtype,
                'type_category': type_category,
                'non_null_count': int(col_data.count()),
                'null_count': int(col_data.isna().sum())
            }

            # Add unique values for categorical columns with few unique values
            if type_category == 'categorical':
                unique_values = col_data.dropna().unique()
                n_unique = len(unique_values)
                col_info['n_unique'] = n_unique

                if n_unique <= self.MAX_UNIQUE_VALUES_DISPLAY:
                    col_info['unique_values'] = [str(v) for v in unique_values[:self.MAX_UNIQUE_VALUES_DISPLAY]]

            # Add basic stats for numeric columns
            if type_category == 'numeric':
                col_info['stats'] = self._get_column_stats(col_data)

            columns.append(col_info)

        self._column_info = columns
        return columns

    def _get_column_stats(self, col: pd.Series) -> Dict[str, Any]:
        """Get summary statistics for a numeric column"""
        try:
            stats = {
                'min': self._safe_value(col.min()),
                'max': self._safe_value(col.max()),
                'mean': self._safe_value(col.mean()),
                'median': self._safe_value(col.median()),
                'std': self._safe_value(col.std())
            }
            return stats
        except Exception as e:
            logger.warning(f"Could not compute stats for column: {e}")
            return {}

    def _safe_value(self, value) -> Any:
        """Convert numpy types to Python native types for JSON serialization"""
        if pd.isna(value):
            return None
        if isinstance(value, (np.integer, np.floating)):
            if np.isnan(value) or np.isinf(value):
                return None
            return round(float(value), 4)
        return value

    def _get_head_data(self, n_rows: int) -> Dict[str, Any]:
        """Get the first N rows as a list of dictionaries"""
        head_df = self.df.head(n_rows)

        # Convert to list of lists for easier frontend rendering
        rows = []
        for _, row in head_df.iterrows():
            row_data = []
            for val in row:
                if pd.isna(val):
                    row_data.append(None)
                elif isinstance(val, (np.integer, np.floating)):
                    row_data.append(round(float(val), 4) if not np.isnan(val) else None)
                else:
                    row_data.append(str(val))
            rows.append(row_data)

        return {
            'column_names': self.df.columns.tolist(),
            'rows': rows,
            'displayed_rows': len(rows),
            'total_rows': len(self.df)
        }

    def _get_summary_stats(self) -> Dict[str, Any]:
        """Get overall summary statistics for the dataset"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()

        return {
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols,
            'n_numeric': len(numeric_cols),
            'n_categorical': len(categorical_cols),
            'memory_usage_mb': round(self.df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        }

    def _get_missing_info(self) -> Dict[str, Any]:
        """Get information about missing values"""
        missing_counts = self.df.isna().sum()
        total_cells = len(self.df) * len(self.df.columns)
        total_missing = int(missing_counts.sum())

        # Columns with missing values
        columns_with_missing = []
        for col in self.df.columns:
            missing_count = int(missing_counts[col])
            if missing_count > 0:
                columns_with_missing.append({
                    'column': col,
                    'missing_count': missing_count,
                    'missing_pct': round(missing_count / len(self.df) * 100, 1)
                })

        return {
            'total_missing': total_missing,
            'total_cells': total_cells,
            'missing_pct': round(total_missing / total_cells * 100, 1) if total_cells > 0 else 0,
            'columns_with_missing': columns_with_missing
        }


def generate_preview_from_file(filepath: str, n_rows: int = 10) -> Dict[str, Any]:
    """
    Convenience function to generate preview from a file path

    Args:
        filepath: Path to CSV or Excel file
        n_rows: Number of rows to preview

    Returns:
        Preview dictionary
    """
    try:
        generator = DataPreviewGenerator.from_file(filepath)
        return generator.generate_preview(n_rows)
    except Exception as e:
        logger.error(f"Error generating preview from file: {e}")
        return {
            'success': False,
            'error': str(e)
        }
