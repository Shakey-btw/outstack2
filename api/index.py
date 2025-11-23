import sys
import os

# Add the parent directory to the path so we can import from backend
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import the FastAPI app from backend
from backend.main import app

# Vercel's @vercel/python builder automatically handles ASGI apps
# Just export the app directly
handler = app

