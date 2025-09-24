"""
Vercel serverless function entry point for FastAPI app
"""
import sys
import os

# Add the root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from server.py
from server import app

# Export the app for Vercel
handler = app
