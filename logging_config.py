"""
Centralized Logging Configuration

Provides a consistent logging setup for the entire application.
Separate from StateLogger which is for structured state/metric logging.

Usage:
    from logging_config import setup_logging, get_logger
    
    # Setup once at application start
    setup_logging(level=logging.INFO, debug=False)
    
    # Use in modules
    logger = get_logger(__name__)
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


# Default log directory
DEFAULT_LOG_DIR = Path(__file__).parent / 'data' / 'logs'
DEFAULT_LOG_FILE = 'application.log'


def setup_logging(
    level: int = logging.INFO,
    debug: bool = False,
    log_file: Optional[str] = None,
    log_dir: Optional[Path] = None,
    console: bool = True,
    file_logging: bool = True
) -> None:
    """
    Setup centralized logging configuration.
    
    Args:
        level: Logging level (logging.DEBUG, logging.INFO, etc.)
        debug: If True, sets level to DEBUG regardless of level parameter
        log_file: Name of log file (default: 'application.log')
        log_dir: Directory for log files (default: 'data/logs')
        console: Enable console logging (default: True)
        file_logging: Enable file logging (default: True)
    """
    # Determine log level
    log_level = logging.DEBUG if debug else level
    
    # Setup log directory
    log_directory = log_dir or DEFAULT_LOG_DIR
    log_directory.mkdir(parents=True, exist_ok=True)
    
    # Log file path
    log_file_path = log_directory / (log_file or DEFAULT_LOG_FILE)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels, filter by handlers
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Formatter with microseconds support
    class MicrosecondFormatter(logging.Formatter):
        """Formatter that supports microseconds in timestamps"""
        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Truncate to milliseconds
    
    formatter = MicrosecondFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S.%f'
    )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if file_logging:
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Prevent propagation to avoid duplicate logs
    root_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__ of the module)
    
    Returns:
        Logger instance configured with centralized settings
    """
    return logging.getLogger(name)


def set_log_level(level: int) -> None:
    """
    Change the log level at runtime.
    
    Args:
        level: New logging level (logging.DEBUG, logging.INFO, etc.)
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            handler.setLevel(level)


# Module-level logger (for this module itself)
_logger = logging.getLogger(__name__)


# Initialize logging with sensible defaults if called directly
if __name__ == "__main__":
    setup_logging(level=logging.INFO, debug=False)
    logger = get_logger(__name__)
    
    # Test logging at all levels
    logger.debug("Debug message - only visible if debug=True")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    print("\n✅ Logging configuration test complete")
    print(f"📁 Logs directory: {DEFAULT_LOG_DIR}")
    print(f"📄 Log file: {DEFAULT_LOG_FILE}")

