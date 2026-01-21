
import os
import sys
import time
from flask import Flask
import shutil

# Setup paths
sys.path.append(os.getcwd())

from app.r_engine.subprocess_executor import SubprocessRExecutor
from app.routes.r_exec import r_exec_bp

# 1. Test R Generation
print("Testing R Plot Generation...")
executor = SubprocessRExecutor()
r_code = """
x <- 1:10
y <- x^2
plot(x, y, main="Test JPG")
"""
result = executor.execute(r_code)

if not result.success:
    print("❌ R Execution Failed")
    print(result.error)
    sys.exit(1)

plots = result.plots
if not plots:
    print("❌ No plots generated")
    sys.exit(1)

plot_path = plots[0]
print(f"Plot generated at: {plot_path}")

if not plot_path.endswith('.jpg'):
    print(f"FAIL: Wrong extension: {os.path.basename(plot_path)}")
else:
    print("PASS: File extension is .jpg")

# Check magic bytes for JPEG (FF D8 FF)
with open(plot_path, 'rb') as f:
    header = f.read(3)
    if header == b'\xff\xd8\xff':
        print("PASS: File content is valid JPEG")
    else:
        print(f"FAIL: File content is NOT JPEG (Header: {header})")

# 2. Test Serving logic
print("\nTesting Flask Serving Logic...")
app = Flask(__name__)
# Mock the data directory config if needed
app.config['DATA_DIR'] = 'data' 

app.register_blueprint(r_exec_bp)

# Mock the executor path in the route (since it imports r_executor instance)
# The route imports: from app.r_engine import r_executor
# We need to ensure that r_executor.plot_dir points to our test location
from app.r_engine import r_executor as app_executor
# app_executor should be the same as SubprocessRExecutor if configured correctly
print(f"App Executor Plot Dir: {app_executor.plot_dir}")

filename = os.path.basename(plot_path)

with app.test_client() as client:
    resp = client.get(f'/api/plot/{filename}')
    print(f"Request: /api/plot/{filename}")
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.content_type}")
    
    if resp.status_code == 200 and resp.content_type == 'image/jpeg':
        print("✅ Served correctly as image/jpeg")
    else:
        print("❌ Serving Failed or wrong Content-Type")

print("\nCleaning up...")
# os.remove(plot_path) 
# Keep it for manual inspection if needed
print("Done.")
