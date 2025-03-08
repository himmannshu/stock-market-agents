import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Database directories
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_DIR = os.path.join(DATA_DIR, "db")
CHROMA_DIR = os.path.join(DB_DIR, "chroma")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# ChromaDB settings
CHROMA_SETTINGS = {
    "persist_directory": str(CHROMA_DIR),  # Convert Path to string
    "anonymized_telemetry": False
}
