"""Logging configuration for the application"""
import os
import logging.config
from datetime import datetime

def setup_logging(log_dir: str = "logs"):
    """Setup logging configuration
    
    Args:
        log_dir: Directory to store log files
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"stock_market_agents_{timestamp}.log")
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d:\n%(message)s\n"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": log_file,
                "mode": "a"
            }
        },
        "loggers": {
            "stock_market_agents": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"]
        }
    }
    
    logging.config.dictConfig(config)
