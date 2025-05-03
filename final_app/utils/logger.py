import logging
import sys
from config import LOG_LEVEL

def setup_logger(name='app_logger'):
    """Sets up a basic console logger."""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL.upper())

    # Avoid adding multiple handlers if logger already exists
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# Initialize logger for general use
log = setup_logger()