import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Database directories
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_DIR = os.path.join(DATA_DIR, "db")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# ChromaDB settings
CHROMA_DB_PATH = os.path.join(DB_DIR, "chroma.db")
CHROMA_SETTINGS = {
    "persist_directory": CHROMA_DB_PATH,
    "anonymized_telemetry": False
}

# Cache settings
CACHE_SETTINGS = {
    "directory": os.path.join(os.path.expanduser("~"), ".cache", "stock_market_agents"),
    "default_expiry": 300  # 5 minutes
}

# Database settings
DB_SETTINGS = {
    "directory": os.path.join(os.path.expanduser("~"), ".local", "share", "stock_market_agents", "db")
}

# Create directories if they don't exist
os.makedirs(CACHE_SETTINGS["directory"], exist_ok=True)
os.makedirs(DB_SETTINGS["directory"], exist_ok=True)
