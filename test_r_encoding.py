
import sys
import os
import subprocess

# Add current dir to path to find app module
sys.path.append(os.getcwd())

try:
    from app.r_engine.subprocess_executor import SubprocessRExecutor
    executor = SubprocessRExecutor()
    
    # Test code that outputs special characters
    code = 'cat("Test: ≤ ≥ ≠")'
    
    print("Executing R code...")
    result = executor.execute(code)
    
    print(f"Success: {result.success}")
    print(f"Output Raw: {result.output!r}")
    print(f"Output: {result.output}")
    
    if "≤" in result.output:
        print("✅ UTF-8 Decoding Works!")
    else:
        print("❌ Still Mojibake/Error")
        
except Exception as e:
    print(f"Error: {e}")
