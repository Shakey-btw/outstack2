import sys
import os
import importlib.util
import traceback

# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))
main_py_path = os.path.join(current_dir, "main.py")

# Debug: Print current directory and files
print(f"Current directory: {current_dir}")
print(f"Looking for main.py at: {main_py_path}")
print(f"main.py exists: {os.path.exists(main_py_path)}")

try:
    files = os.listdir(current_dir)
    print(f"Files in directory: {files}")
except Exception as e:
    print(f"Could not list files: {e}")

# Try multiple import strategies
app = None
import_errors = []

# Strategy 1: Use importlib to load main.py directly
if os.path.exists(main_py_path):
    try:
        spec = importlib.util.spec_from_file_location("main", main_py_path)
        if spec and spec.loader:
            main_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_module)
            app = main_module.app
            print("✓ Successfully imported app using importlib")
    except Exception as e1:
        import_errors.append(f"importlib: {str(e1)}")
        print(f"importlib failed: {e1}")

# Strategy 2: Try relative import
if app is None:
    try:
        from .main import app
        print("✓ Successfully imported app from .main (relative import)")
    except (ImportError, ValueError, SystemError) as e2:
        import_errors.append(f"from .main: {str(e2)}")

# Strategy 3: Add current dir to path and import
if app is None:
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    try:
        import main
        app = main.app
        print("✓ Successfully imported app from main (after adding to path)")
    except ImportError as e3:
        import_errors.append(f"from main: {str(e3)}")

# Strategy 4: Try api.main
if app is None:
    try:
        from api.main import app
        print("✓ Successfully imported app from api.main")
    except ImportError as e4:
        import_errors.append(f"from api.main: {str(e4)}")

# If all strategies failed
if app is None:
    error_msg = f"Failed to import app from any location:\n"
    for err in import_errors:
        error_msg += f"  {err}\n"
    error_msg += f"  Current dir: {current_dir}\n"
    error_msg += f"  main.py path: {main_py_path}\n"
    error_msg += f"  main.py exists: {os.path.exists(main_py_path)}\n"
    error_msg += f"  Python path: {sys.path}\n"
    try:
        error_msg += f"  Files in dir: {os.listdir(current_dir)}\n"
    except:
        error_msg += f"  Could not list files in dir\n"
    error_msg += f"  Traceback: {traceback.format_exc()}"
    print(error_msg)
    raise ImportError(error_msg)

# Use Mangum to wrap the FastAPI app for Vercel serverless functions
# Mangum is an ASGI adapter for AWS Lambda and Vercel
try:
    from mangum import Mangum
    # Create the handler with Mangum
    # lifespan="off" disables FastAPI lifespan events which can cause issues in serverless
    handler = Mangum(app, lifespan="off")
    print("Successfully created Mangum handler")
except Exception as e:
    print(f"Error creating Mangum handler: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    # Fallback to direct app export (Vercel might handle it)
    handler = app
    print("Falling back to direct app export")

