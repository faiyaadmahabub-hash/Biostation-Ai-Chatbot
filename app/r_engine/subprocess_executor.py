"""
R Executor using subprocess - Alternative to rpy2 for Windows
Executes R code by calling Rscript directly via subprocess.
"""

import os
import subprocess
import tempfile
import logging
from typing import Optional
from .executor import RExecutionResult

logger = logging.getLogger(__name__)


class SubprocessRExecutor:
    """Execute R code using subprocess (works on Windows!)"""
    
    def __init__(self):
        self.rscript_path = self._find_rscript()
        self.available = self.rscript_path is not None
        
        # Set up temp and plot directories
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.temp_dir = os.path.join(base_dir, "data", "temp_r")
        self.plot_dir = os.path.join(base_dir, "data", "plots")
        
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.plot_dir, exist_ok=True)
        
        if self.available:
            logger.info(f"R found at: {self.rscript_path}")
        else:
            logger.warning("Rscript not found. R execution unavailable.")
    
    def _find_rscript(self) -> Optional[str]:
        """Find Rscript executable on the system"""
        # Common Windows locations
        common_paths = [
            r"C:\Program Files\R\R-4.4.2\bin\Rscript.exe",
            r"C:\Program Files\R\R-4.3.2\bin\Rscript.exe",
            r"C:\Program Files\R\R-4.3.1\bin\Rscript.exe",
            r"C:\Program Files\R\R-4.2.3\bin\Rscript.exe",
            r"C:\Program Files (x86)\R\R-4.4.2\bin\Rscript.exe",
        ]
        
        # Check common paths
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(
                ["where", "Rscript"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        # Search Program Files
        try:
            r_base = r"C:\Program Files\R"
            if os.path.exists(r_base):
                for folder in os.listdir(r_base):
                    rscript = os.path.join(r_base, folder, "bin", "Rscript.exe")
                    if os.path.exists(rscript):
                        return rscript
        except:
            pass
        
        return None
    
    def execute(self, code: str, capture_plots: bool = True, timeout: int = 60) -> RExecutionResult:
        """
        Execute R code and return results.
        
        Args:
            code: R code to execute
            capture_plots: Whether to capture plots (ignored as wrapper handles it)
            timeout: Maximum execution time in seconds
        
        Returns:
            RExecutionResult compatible object
        """
        if not self.available:
            return RExecutionResult(
                success=False,
                output="",
                errors="R is not installed or not found. Please install R from https://cran.r-project.org/",
                warnings="",
                plots=[]
            )
        
        # Create temp file for code
        import time
        timestamp = int(time.time() * 1000)
        script_file = os.path.join(self.temp_dir, f"script_{timestamp}.R")
        plot_file = os.path.join(self.plot_dir, f"plot_{timestamp}.jpg")
        
        # Add plot output wrapper if code might generate plots
        plot_setup = f'''
# Set up jpeg output for any plots
jpeg("{plot_file.replace(os.sep, '/')}", width=800, height=600, quality=90)
'''
        plot_teardown = '''
# Close graphics device if open
if (!is.null(dev.list())) invisible(dev.off())
'''

        # Helper R function to check and install packages
        pkg_helper = '''
# Function to ensure packages are installed
ensure_package <- function(pkg) {
  if (!require(pkg, character.only = TRUE)) {
    cat(paste("Installing missing package:", pkg, "\\n"))
    install.packages(pkg, repos = "https://cloud.r-project.org")
    if (!require(pkg, character.only = TRUE)) {
      stop(paste("Failed to install package:", pkg))
    }
  }
}
'''
        
        # Inject package checks for any library() calls in the code
        import re
        
        # Find all library calls: library(pkg) or library("pkg") or library('pkg')
        # We capture the package name
        lib_pattern = re.compile(r'library\s*\(\s*["\']?([a-zA-Z0-9\.]+)["\']?\s*\)')
        
        # Replace library(pkg) with ensure_package("pkg"); library(pkg)
        # using a function to handle quotes correctly
        def replace_lib(match):
            pkg = match.group(1)
            return f'ensure_package("{pkg}"); library({pkg})'
        
        processed_code = lib_pattern.sub(replace_lib, code)
        
        # Wrap code with plot capture and helper
        full_code = pkg_helper + plot_setup + processed_code + plot_teardown
        
        try:
            # Write code to temp file
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(full_code)
            
            # Prepare environment with UTF-8 encoding
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["LC_ALL"] = "en_US.UTF-8"
            env["LANG"] = "en_US.UTF-8"

            # Execute R script
            result = subprocess.run(
                [self.rscript_path, "--vanilla", script_file],
                capture_output=True,
                text=False,  # Capture as bytes to decode manually
                timeout=timeout,
                cwd=self.temp_dir,
                env=env
            )
            
            # Decode with error handling to prevent crashes on special chars
            output = result.stdout.decode('utf-8', errors='replace')
            errors = result.stderr.decode('utf-8', errors='replace')
            
            # Check if plot was created
            plots = []
            if os.path.exists(plot_file) and os.path.getsize(plot_file) > 1000:
                plots.append(plot_file)
            elif os.path.exists(plot_file):
                # Remove empty plot file
                try:
                    os.remove(plot_file)
                except:
                    pass
            
            # Clean up script file
            try:
                os.remove(script_file)
            except:
                pass
            
            return RExecutionResult(
                success=result.returncode == 0,
                output=output,
                errors=errors,
                warnings="",  # Rscript stderr typically contains warnings too
                plots=plots
            )
        
        except subprocess.TimeoutExpired:
            return RExecutionResult(
                success=False,
                output="",
                errors=f"R code execution timed out after {timeout} seconds",
                warnings="",
                plots=[]
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
        finally:
            # Cleanup
            if os.path.exists(script_file):
                try:
                    os.remove(script_file)
                except:
                    pass


# Singleton instance
subprocess_r_executor = SubprocessRExecutor()
