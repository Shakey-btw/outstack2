import sys
import os
import importlib.util

try:
    # Get the absolute paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    backend_main_path = os.path.join(parent_dir, 'backend', 'main.py')
    
    # Debug: print paths (will show in Vercel logs)
    print(f"Current dir: {current_dir}")
    print(f"Parent dir: {parent_dir}")
    print(f"Backend main path: {backend_main_path}")
    print(f"Backend main exists: {os.path.exists(backend_main_path)}")
    
    # Add parent directory to path
    sys.path.insert(0, parent_dir)
    
    # Use importlib to load the module (more reliable on Vercel)
    spec = importlib.util.spec_from_file_location("backend.main", backend_main_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load backend.main from {backend_main_path}")
    
    backend_main = importlib.util.module_from_spec(spec)
    sys.modules["backend.main"] = backend_main
    spec.loader.exec_module(backend_main)
    
    # Get the app from the loaded module
    app = backend_main.app
    
    print("Successfully loaded backend.main")
    
except Exception as e:
    # Log the error for debugging in Vercel
    import traceback
    error_msg = f"Error loading backend.main: {str(e)}\n{traceback.format_exc()}"
    print(error_msg)
    raise ImportError(error_msg)

# Vercel's @vercel/python builder automatically handles ASGI apps
handler = app

