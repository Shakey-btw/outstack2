import sys
import os

# Add the parent directory to the path so we can import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from vercel_func_adapter import VercelASGIHandler

handler = VercelASGIHandler(app)

