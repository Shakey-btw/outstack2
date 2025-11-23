import sys
import os
import traceback

# Add the parent directory to the path so we can import from backend
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from backend.main import app
except ImportError as e:
    # Fallback: try importing from api/main if backend/main doesn't work
    try:
        from api.main import app
    except ImportError as e2:
        error_msg = f"Could not import app from backend.main or api.main.\n"
        error_msg += f"backend.main error: {str(e)}\n"
        error_msg += f"api.main error: {str(e2)}\n"
        error_msg += f"Project root: {project_root}\n"
        error_msg += f"Python path: {sys.path}\n"
        error_msg += f"Traceback: {traceback.format_exc()}"
        print(error_msg)
        raise ImportError(error_msg)

# Use Mangum to wrap the FastAPI app for Vercel serverless functions
try:
    from mangum import Mangum
    # Create the handler with Mangum
    handler = Mangum(app, lifespan="off")
except Exception as e:
    # If Mangum fails, try using the app directly (Vercel might handle it)
    print(f"Warning: Could not create Mangum handler: {e}")
    print("Falling back to direct app export")
    handler = app

