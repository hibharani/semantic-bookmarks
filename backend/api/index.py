import os
import sys

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database and models to ensure tables are created
from database import engine, Base
from models import User, Bookmark, Embedding, SearchLog

# Create tables if they don't exist
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database initialization warning: {e}")

# Import the configured app
from main import app

# Export the app for Vercel
handler = app