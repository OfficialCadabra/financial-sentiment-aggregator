import logging
import os
import sys
from datetime import datetime

def setup_logger(level=logging.INFO):
    """
    Set up logger with console and file handlers.
    
    Args:
        level: Logging level (default: INFO)
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join('logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Logger configuration
    log_filename = os.path.join(log_dir, f'news_aggregator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Log basic system info
    root_logger.info(f"Logging to {log_filename}")
    root_logger.info(f"Log level: {logging.getLevelName(level)}")
    
    return root_logger