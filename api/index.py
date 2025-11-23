import sys
import os
import traceback

# Add current directory to Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Try multiple import strategies to ensure the app is found
app = None
import_errors = []

try:
    # First try: import from main in same directory
    from main import app
    print("✓ Successfully imported app from main")
except ImportError as e1:
    import_errors.append(f"from main: {str(e1)}")
    try:
        # Second try: import from api.main
        from api.main import app
        print("✓ Successfully imported app from api.main")
    except ImportError as e2:
        import_errors.append(f"from api.main: {str(e2)}")
        # If all imports fail, raise with detailed error
        error_msg = f"Failed to import app from any location:\n"
        for err in import_errors:
            error_msg += f"  {err}\n"
        error_msg += f"  Current dir: {current_dir}\n"
        error_msg += f"  Python path: {sys.path}\n"
        try:
            error_msg += f"  Files in dir: {os.listdir(current_dir)}\n"
        except:
            error_msg += f"  Could not list files in dir\n"
        error_msg += f"  Traceback: {traceback.format_exc()}"
        print(error_msg)
        raise ImportError(error_msg)

if app is None:
    raise ImportError("App is None after import attempts")

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

