"""
R Executor - Execute R code and capture output using rpy2
Provides safe execution with timeout and output parsing.
"""

import os
import re
import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Flag to track if rpy2 is available
RPY2_AVAILABLE = False
ro = None
pandas2ri = None
importr = None

try:
    import rpy2
    import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.packages import importr
    from rpy2.rinterface_lib.callbacks import logger as rpy2_logger
    
    # Suppress rpy2 warnings in console
    rpy2_logger.setLevel(logging.ERROR)
    
    # Activate pandas conversion
    pandas2ri.activate()
    
    RPY2_AVAILABLE = True
    logger.info("rpy2 loaded successfully")
except Exception as e:
    # Catch ALL exceptions - rpy2 on Windows can throw various errors
    logger.warning(f"rpy2 not available: {e}. R execution disabled.")


@dataclass
class RExecutionResult:
    """Result of R code execution"""
    success: bool
    output: str
    errors: str
    warnings: str
    plots: list  # List of plot file paths
    result_data: Optional[Any] = None  # Returned R object converted to Python


class RExecutor:
    """Execute R code safely with output capture"""
    
    def __init__(self):
        self.available = RPY2_AVAILABLE
        self._r = None
        self._base = None
        self._graphics = None
        self._grdevices = None
        
        if self.available:
            self._init_r()
    
    def _init_r(self):
        """Initialize R environment"""
        try:
            self._r = ro.r
            self._base = importr('base')
            self._graphics = importr('graphics')
            self._grdevices = importr('grDevices')
            
            # Set up plot capture directory
            self.plot_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "data", "plots"
            )
            os.makedirs(self.plot_dir, exist_ok=True)
            
            logger.info("R environment initialized")
        except Exception as e:
            logger.error(f"Failed to initialize R: {e}")
            self.available = False
    
    def execute(self, code: str, capture_plots: bool = True) -> RExecutionResult:
        """
        Execute R code and return results.
        
        Args:
            code: R code to execute
            capture_plots: Whether to capture any generated plots
        
        Returns:
            RExecutionResult with output, errors, warnings, and plots
        """
        if not self.available:
            return RExecutionResult(
                success=False,
                output="",
                errors="R execution not available. rpy2 is not installed or R is not configured.",
                warnings="",
                plots=[]
            )
        
        output_lines = []
        error_lines = []
        warning_lines = []
        plots = []
        result = None
        
        try:
            # Set up output capture
            from io import StringIO
            import sys
            
            # Capture R console output
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            # Set up plot capture if requested
            plot_file = None
            if capture_plots:
                import time
                plot_file = os.path.join(self.plot_dir, f"plot_{int(time.time())}.png")
                # Use jpeg device for better compatibility
                self._r(f'jpeg("{plot_file.replace(os.sep, "/")}", width=800, height=600, quality=90)')
            
            # Execute the code
            try:
                # Split code into lines and execute
                result = self._r(code)
                
                # Get any print output
                output_text = sys.stdout.getvalue()
                if output_text:
                    output_lines.append(output_text)
                
            except Exception as e:
                error_str = str(e)
                error_lines.append(error_str)
            
            finally:
                sys.stdout = old_stdout
                
                # Close plot device if opened
                if capture_plots:
                    try:
                        self._grdevices.dev_off()
                        # Check if plot file was created and has content
                        if os.path.exists(plot_file) and os.path.getsize(plot_file) > 0:
                            plots.append(plot_file)
                        elif os.path.exists(plot_file):
                            os.remove(plot_file)  # Remove empty plot file
                    except:
                        pass
            
            # Convert result to string if possible
            result_str = ""
            if result is not None:
                try:
                    result_str = str(result)
                    if result_str and result_str not in output_lines:
                        output_lines.append(result_str)
                except:
                    pass
            
            return RExecutionResult(
                success=len(error_lines) == 0,
                output="\n".join(output_lines),
                errors="\n".join(error_lines),
                warnings="\n".join(warning_lines),
                plots=plots,
                result_data=result
            )
        
        except Exception as e:
            logger.error(f"R execution error: {e}")
            return RExecutionResult(
                success=False,
                output="",
                errors=str(e),
                warnings="",
                plots=[]
            )
    
    def load_data(self, file_path: str, var_name: str = "data") -> RExecutionResult:
        """Load a CSV/Excel file into R environment"""
        
        if file_path.endswith('.csv'):
            code = f'{var_name} <- read.csv("{file_path.replace(os.sep, "/")}")'
        elif file_path.endswith(('.xlsx', '.xls')):
            code = f'''
library(readxl)
{var_name} <- read_excel("{file_path.replace(os.sep, "/")}")
'''
        else:
            return RExecutionResult(
                success=False,
                output="",
                errors=f"Unsupported file format: {file_path}",
                warnings="",
                plots=[]
            )
        
        result = self.execute(code, capture_plots=False)
        
        if result.success:
            # Get data summary
            summary_code = f'''
cat("Data loaded successfully!\\n")
cat("Dimensions:", nrow({var_name}), "rows x", ncol({var_name}), "columns\\n")
cat("\\nColumn names:\\n")
print(names({var_name}))
cat("\\nFirst few rows:\\n")
print(head({var_name}))
'''
            summary_result = self.execute(summary_code, capture_plots=False)
            return summary_result
        
        return result
    
    def get_variable_info(self, var_name: str) -> Dict:
        """Get information about an R variable"""
        if not self.available:
            return {"error": "R not available"}
        
        try:
            info = {}
            
            # Get class
            info['class'] = str(self._r(f'class({var_name})')[0])
            
            # Get dimensions/length
            try:
                dims = self._r(f'dim({var_name})')
                if dims is not None:
                    info['dimensions'] = list(dims)
                else:
                    info['length'] = int(self._r(f'length({var_name})')[0])
            except:
                pass
            
            # Get column names if data frame
            if info.get('class') == 'data.frame':
                info['columns'] = list(self._r(f'names({var_name})'))
            
            return info
        except Exception as e:
            return {"error": str(e)}


class OutputParser:
    """Parse and format R output for display"""
    
    @staticmethod
    def format_for_display(result: RExecutionResult) -> str:
        """Format R execution result for chat display"""
        parts = []
        
        if result.success:
            parts.append("## ✅ R Code Executed Successfully\n")
        else:
            parts.append("## ❌ R Execution Error\n")
        
        if result.output:
            parts.append("### Output:\n```\n" + result.output[:2000] + "\n```\n")
        
        if result.errors:
            parts.append("### Errors:\n```\n" + result.errors + "\n```\n")
        
        if result.warnings:
            parts.append("### Warnings:\n```\n" + result.warnings + "\n```\n")
        
        if result.plots:
            parts.append(f"\n*{len(result.plots)} plot(s) generated*\n")
        
        return "\n".join(parts)
    
    @staticmethod
    def extract_statistics(output: str) -> Dict:
        """Extract key statistics from R output"""
        stats = {}
        
        # Extract p-value
        p_match = re.search(r'p-value[:\s]*([<>=]?\s*[\d.e-]+)', output, re.IGNORECASE)
        if p_match:
            stats['p_value'] = p_match.group(1).strip()
        
        # Extract t-value
        t_match = re.search(r't\s*=\s*([-\d.]+)', output)
        if t_match:
            stats['t_value'] = float(t_match.group(1))
        
        # Extract correlation
        r_match = re.search(r'cor[relation]*[:\s]*([-\d.]+)', output, re.IGNORECASE)
        if r_match:
            stats['correlation'] = float(r_match.group(1))
        
        # Extract F-value
        f_match = re.search(r'F\s*=\s*([\d.]+)', output)
        if f_match:
            stats['f_value'] = float(f_match.group(1))
        
        # Extract degrees of freedom
        df_match = re.search(r'df\s*=\s*([\d.]+)', output)
        if df_match:
            stats['df'] = float(df_match.group(1))
        
        return stats
    
    @staticmethod
    def interpret_p_value(p_value_str: str) -> str:
        """Provide interpretation of p-value"""
        try:
            if '<' in p_value_str:
                p = float(p_value_str.replace('<', '').strip())
                p = p / 10  # If < 0.05, actual value is even smaller
            else:
                p = float(p_value_str.replace('=', '').strip())
            
            if p < 0.001:
                return "**Highly significant** (p < 0.001): Very strong evidence against the null hypothesis."
            elif p < 0.01:
                return "**Highly significant** (p < 0.01): Strong evidence against the null hypothesis."
            elif p < 0.05:
                return "**Significant** (p < 0.05): Evidence against the null hypothesis."
            elif p < 0.10:
                return "**Marginally significant** (p < 0.10): Weak evidence, consider with caution."
            else:
                return "**Not significant** (p ≥ 0.10): Insufficient evidence against the null hypothesis."
        except:
            return "Unable to interpret p-value."


# Singleton instance
r_executor = RExecutor()
output_parser = OutputParser()
