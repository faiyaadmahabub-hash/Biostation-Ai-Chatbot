"""
Built-in Dataset Library Module

Provides classic statistical datasets for learning and practice.
"""

from .registry import DatasetRegistry, get_dataset_registry
from .loader import DatasetLoader, get_dataset_loader

__all__ = [
    'DatasetRegistry',
    'get_dataset_registry',
    'DatasetLoader',
    'get_dataset_loader',
]
