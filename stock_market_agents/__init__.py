"""Stock Market Research Agents Package"""
import os
from .config.logging import setup_logging

# Set up logging with default log directory
setup_logging(os.path.join(os.path.dirname(__file__), "..", "logs"))