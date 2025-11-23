# Import the app directly from main.py in the same directory
from main import app

# Vercel's @vercel/python builder automatically handles ASGI apps
handler = app

