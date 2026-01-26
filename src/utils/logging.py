import logging
import sys
from ..config import settings


def setup_logging() -> None:
    """Configure logging for the application."""
    
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured - Level: {logging.getLevelName(log_level)}")
