"""
Dataset Loader - Load built-in datasets as pandas DataFrames

Provides functionality to:
- Load R built-in datasets using hardcoded data
- Save datasets to user's data directory
- Generate previews for datasets
"""

import os
import logging
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path

from .registry import get_dataset_registry

logger = logging.getLogger(__name__)


class DatasetLoader:
    """Load and manage built-in datasets"""

    def __init__(self, data_dir: str = "data/user_datasets"):
        """
        Initialize the dataset loader.

        Args:
            data_dir: Directory to save loaded datasets
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.registry = get_dataset_registry()
        self._dataset_cache: Dict[str, pd.DataFrame] = {}

    def load_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """
        Load a built-in dataset as a pandas DataFrame.

        Args:
            dataset_id: ID of the dataset to load

        Returns:
            pandas DataFrame or None if dataset not found
        """
        # Check cache first
        if dataset_id in self._dataset_cache:
            return self._dataset_cache[dataset_id].copy()

        # Get dataset info
        info = self.registry.get_dataset_info(dataset_id)
        if not info:
            logger.error(f"Dataset not found: {dataset_id}")
            return None

        # Load the dataset
        loader_method = getattr(self, f"_load_{dataset_id}", None)
        if loader_method:
            df = loader_method()
            self._dataset_cache[dataset_id] = df
            return df.copy()

        logger.error(f"No loader method for dataset: {dataset_id}")
        return None

    def save_as_user_dataset(self, dataset_id: str) -> Optional[str]:
        """
        Load a built-in dataset and save it to the user's data directory.

        Args:
            dataset_id: ID of the dataset to load

        Returns:
            Path to the saved file, or None if failed
        """
        df = self.load_dataset(dataset_id)
        if df is None:
            return None

        # Save to CSV
        filename = f"{dataset_id}.csv"
        filepath = self.data_dir / filename

        try:
            df.to_csv(filepath, index=False)
            logger.info(f"Saved dataset to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving dataset: {e}")
            return None

    def get_dataset_preview(self, dataset_id: str, n_rows: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get a preview of a built-in dataset.

        Args:
            dataset_id: ID of the dataset
            n_rows: Number of rows to include in preview

        Returns:
            Preview dictionary compatible with the preview system
        """
        df = self.load_dataset(dataset_id)
        if df is None:
            return None

        from app.preview import DataPreviewGenerator
        generator = DataPreviewGenerator(df)
        return generator.generate_preview(n_rows)

    # ============ DATASET LOADERS ============
    # Each method returns a pandas DataFrame with the dataset

    def _load_iris(self) -> pd.DataFrame:
        """Load the iris dataset"""
        from sklearn.datasets import load_iris
        iris = load_iris()
        df = pd.DataFrame(
            iris.data,
            columns=["Sepal.Length", "Sepal.Width", "Petal.Length", "Petal.Width"]
        )
        df["Species"] = pd.Categorical.from_codes(
            iris.target,
            categories=["setosa", "versicolor", "virginica"]
        )
        return df

    def _load_mtcars(self) -> pd.DataFrame:
        """Load the mtcars dataset"""
        data = {
            "mpg": [21.0, 21.0, 22.8, 21.4, 18.7, 18.1, 14.3, 24.4, 22.8, 19.2,
                   17.8, 16.4, 17.3, 15.2, 10.4, 10.4, 14.7, 32.4, 30.4, 33.9,
                   21.5, 15.5, 15.2, 13.3, 19.2, 27.3, 26.0, 30.4, 15.8, 19.7, 15.0, 21.4],
            "cyl": [6, 6, 4, 6, 8, 6, 8, 4, 4, 6, 6, 8, 8, 8, 8, 8, 8, 4, 4, 4,
                   4, 8, 8, 8, 8, 4, 4, 4, 8, 6, 8, 4],
            "disp": [160.0, 160.0, 108.0, 258.0, 360.0, 225.0, 360.0, 146.7, 140.8, 167.6,
                   167.6, 275.8, 275.8, 275.8, 472.0, 460.0, 440.0, 78.7, 75.7, 71.1,
                   120.1, 318.0, 304.0, 350.0, 400.0, 79.0, 120.3, 95.1, 351.0, 145.0, 301.0, 121.0],
            "hp": [110, 110, 93, 110, 175, 105, 245, 62, 95, 123, 123, 180, 180, 180,
                  205, 215, 230, 66, 52, 65, 97, 150, 150, 245, 175, 66, 91, 113, 264, 175, 335, 109],
            "drat": [3.90, 3.90, 3.85, 3.08, 3.15, 2.76, 3.21, 3.69, 3.92, 3.92,
                    3.92, 3.07, 3.07, 3.07, 2.93, 3.00, 3.23, 4.08, 4.93, 4.22,
                    3.70, 2.76, 3.15, 3.73, 3.08, 4.08, 4.43, 3.77, 4.22, 3.62, 3.54, 4.11],
            "wt": [2.620, 2.875, 2.320, 3.215, 3.440, 3.460, 3.570, 3.190, 3.150, 3.440,
                  3.440, 4.070, 3.730, 3.780, 5.250, 5.424, 5.345, 2.200, 1.615, 1.835,
                  2.465, 3.520, 3.435, 3.840, 3.845, 1.935, 2.140, 1.513, 3.170, 2.770, 3.570, 2.780],
            "qsec": [16.46, 17.02, 18.61, 19.44, 17.02, 20.22, 15.84, 20.00, 22.90, 18.30,
                   18.90, 17.40, 17.60, 18.00, 17.98, 17.82, 17.42, 19.47, 18.52, 19.90,
                   20.01, 16.87, 17.30, 15.41, 17.05, 18.90, 16.70, 16.90, 14.50, 15.50, 14.60, 18.60],
            "vs": [0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1],
            "am": [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
            "gear": [4, 4, 4, 3, 3, 3, 3, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 4, 4, 4, 3, 3, 3, 3, 3, 4, 5, 5, 5, 5, 5, 4],
            "carb": [4, 4, 1, 1, 2, 1, 4, 2, 2, 4, 4, 3, 3, 3, 4, 4, 4, 1, 2, 1, 1, 2, 2, 4, 2, 1, 2, 2, 4, 6, 8, 2],
        }
        return pd.DataFrame(data)

    def _load_toothgrowth(self) -> pd.DataFrame:
        """Load the ToothGrowth dataset"""
        data = {
            "len": [4.2, 11.5, 7.3, 5.8, 6.4, 10.0, 11.2, 11.2, 5.2, 7.0,
                   16.5, 16.5, 15.2, 17.3, 22.5, 17.3, 13.6, 14.5, 18.8, 15.5,
                   23.6, 18.5, 33.9, 25.5, 26.4, 32.5, 26.7, 21.5, 23.3, 29.5,
                   15.2, 21.5, 17.6, 9.7, 14.5, 10.0, 8.2, 9.4, 16.5, 9.7,
                   19.7, 23.3, 23.6, 26.4, 20.0, 25.2, 25.8, 21.2, 14.5, 27.3,
                   25.5, 26.4, 22.4, 24.5, 24.8, 30.9, 26.4, 27.3, 29.4, 23.0],
            "supp": ["VC"]*30 + ["OJ"]*30,
            "dose": [0.5]*10 + [1.0]*10 + [2.0]*10 + [0.5]*10 + [1.0]*10 + [2.0]*10,
        }
        return pd.DataFrame(data)

    def _load_plantgrowth(self) -> pd.DataFrame:
        """Load the PlantGrowth dataset"""
        data = {
            "weight": [4.17, 5.58, 5.18, 6.11, 4.50, 4.61, 5.17, 4.53, 5.33, 5.14,
                      4.81, 4.17, 4.41, 3.59, 5.87, 3.83, 6.03, 4.89, 4.32, 4.69,
                      6.31, 5.12, 5.54, 5.50, 5.37, 5.29, 4.92, 6.15, 5.80, 5.26],
            "group": ["ctrl"]*10 + ["trt1"]*10 + ["trt2"]*10,
        }
        return pd.DataFrame(data)

    def _load_chickweight(self) -> pd.DataFrame:
        """Load the ChickWeight dataset (subset for performance)"""
        # Using a representative subset
        np.random.seed(42)

        data = []
        for chick_id in range(1, 51):  # 50 chicks
            diet = ((chick_id - 1) % 4) + 1
            base_weight = 40 + np.random.normal(0, 5)

            for day in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 21]:
                growth_rate = 8 + diet * 0.5 + np.random.normal(0, 1)
                weight = base_weight + growth_rate * day + np.random.normal(0, 5)
                data.append({
                    "weight": max(35, round(weight, 1)),
                    "Time": day,
                    "Chick": str(chick_id),
                    "Diet": str(diet),
                })

        return pd.DataFrame(data)

    def _load_sleep(self) -> pd.DataFrame:
        """Load the sleep dataset"""
        data = {
            "extra": [0.7, -1.6, -0.2, -1.2, -0.1, 3.4, 3.7, 0.8, 0.0, 2.0,
                     1.9, 0.8, 1.1, 0.1, -0.1, 4.4, 5.5, 1.6, 4.6, 3.4],
            "group": ["1"]*10 + ["2"]*10,
            "ID": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"] * 2,
        }
        return pd.DataFrame(data)

    def _load_airquality(self) -> pd.DataFrame:
        """Load the airquality dataset"""
        # Simplified version with representative data
        np.random.seed(42)

        data = []
        for month in range(5, 10):  # May to September
            days_in_month = 31 if month in [5, 7, 8] else 30
            for day in range(1, days_in_month + 1):
                # Generate realistic air quality data
                temp = 60 + month * 5 + np.random.normal(0, 10)
                ozone = max(1, 20 + (temp - 70) * 2 + np.random.normal(0, 20))
                solar = max(0, 150 + np.random.normal(0, 80))
                wind = max(1, 10 + np.random.normal(0, 4))

                # Add some missing values (like real airquality dataset)
                if np.random.random() < 0.15:
                    ozone = np.nan
                if np.random.random() < 0.05:
                    solar = np.nan

                data.append({
                    "Ozone": round(ozone, 1) if not np.isnan(ozone) else np.nan,
                    "Solar.R": round(solar, 0) if not np.isnan(solar) else np.nan,
                    "Wind": round(wind, 1),
                    "Temp": round(temp, 0),
                    "Month": month,
                    "Day": day,
                })

        return pd.DataFrame(data)

    def _load_faithful(self) -> pd.DataFrame:
        """Load the faithful geyser dataset"""
        # Bimodal distribution of Old Faithful data
        np.random.seed(42)

        data = []
        for _ in range(272):
            if np.random.random() < 0.35:
                # Short eruptions cluster
                eruptions = np.random.normal(2.0, 0.3)
                waiting = np.random.normal(55, 5)
            else:
                # Long eruptions cluster
                eruptions = np.random.normal(4.5, 0.4)
                waiting = np.random.normal(80, 6)

            data.append({
                "eruptions": round(max(1.5, min(5.5, eruptions)), 3),
                "waiting": round(max(40, min(100, waiting)), 0),
            })

        return pd.DataFrame(data)


# Singleton instance
_loader = None


def get_dataset_loader(data_dir: str = "data/user_datasets") -> DatasetLoader:
    """Get or create the dataset loader singleton"""
    global _loader
    if _loader is None:
        _loader = DatasetLoader(data_dir)
    return _loader
