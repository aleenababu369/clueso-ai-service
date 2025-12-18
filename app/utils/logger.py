"""
Logging utility for the AI Service.
Provides structured logging with timestamps and levels.
"""

import logging
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = "ai-service",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure a logger.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional file path for logging
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = ColoredFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


# Global logger instance
logger = setup_logger("ai-service", logging.DEBUG)


def log_request(endpoint: str, data_size: int) -> None:
    """Log an incoming API request."""
    logger.info(f"📥 Request: {endpoint} | Data size: {data_size} bytes")


def log_processing_time(operation: str, duration_ms: float) -> None:
    """Log processing time for an operation."""
    logger.info(f"⏱️  {operation} completed in {duration_ms:.2f}ms")


def log_error(operation: str, error: Exception) -> None:
    """Log an error with context."""
    logger.error(f"❌ {operation} failed: {str(error)}", exc_info=True)


def log_success(operation: str, details: str = "") -> None:
    """Log a successful operation."""
    msg = f"✅ {operation} successful"
    if details:
        msg += f" | {details}"
    logger.info(msg)
