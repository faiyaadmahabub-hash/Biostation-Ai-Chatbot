"""R Engine module initialization"""
from .executor import RExecutor, RExecutionResult, OutputParser, output_parser, r_executor as _rpy2_executor
from .subprocess_executor import subprocess_r_executor
from .validator import DataValidator, ValidationResult, data_validator
from .error_analyzer import analyze_r_error, get_fix_for_template
import logging

logger = logging.getLogger(__name__)

# Choose the best available executor
if _rpy2_executor.available:
    r_executor = _rpy2_executor
    logger.info("Using rpy2-based R executor")
else:
    r_executor = subprocess_r_executor
    logger.info("Using subprocess-based R executor (rpy2 unavailable)")

__all__ = [
    'RExecutor',
    'RExecutionResult',
    'OutputParser',
    'r_executor',
    'output_parser',
    'DataValidator',
    'ValidationResult',
    'data_validator',
    'analyze_r_error',
    'get_fix_for_template'
]
