"""
Centralized Logging Configuration for Audio Summary App

Import this module at the start of any entry point to ensure
consistent logging across the application.

Usage:
    from app_logging import logger, setup_logging

    # At app startup
    setup_logging()

    # Throughout the app
    logger.info("Message")
    logger.error("Error occurred", exc_info=True)
"""
import logging
import logging.handlers
import os
from datetime import datetime

# Create logger instance
logger = logging.getLogger("AudioSummaryApp")

# Prevent duplicate logging - don't propagate to root logger
logger.propagate = False

# Track if logging has been set up
_logging_configured = False


def setup_logging(
    log_file: str = "app_debug.log",
    level: int = logging.DEBUG,
    max_bytes: int = 5 * 1024 * 1024,  # 5MB
    backup_count: int = 3,
    console_output: bool = True
):
    """
    Configure logging for the application.

    Args:
        log_file: Path to the log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Max size before rotation (default 5MB)
        backup_count: Number of backup files to keep
        console_output: Whether to also log to console
    """
    global _logging_configured

    if _logging_configured:
        logger.debug("Logging already configured, skipping")
        return logger

    # Set level
    logger.setLevel(level)

    # Log format
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}")

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Less verbose on console
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    _logging_configured = True

    # Log startup
    logger.info("=" * 60)
    logger.info(f"Application started at {datetime.now().isoformat()}")
    logger.info("=" * 60)

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Optional name for a child logger (e.g., "AudioSummaryApp.backend")

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"AudioSummaryApp.{name}")
    return logger


# Convenience functions for quick logging
def log_event(event_type: str, details: dict = None):
    """Log a structured event"""
    msg = f"EVENT: {event_type}"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        msg += f" | {detail_str}"
    logger.info(msg)


def log_recording_start(mode: str, device: str):
    """Log recording start event"""
    log_event("RECORDING_START", {"mode": mode, "device": device})


def log_recording_stop(duration_seconds: float):
    """Log recording stop event"""
    log_event("RECORDING_STOP", {"duration_seconds": round(duration_seconds, 2)})


def log_transcription(status: str, word_count: int = None):
    """Log transcription event"""
    details = {"status": status}
    if word_count:
        details["word_count"] = word_count
    log_event("TRANSCRIPTION", details)


def log_ai_request(provider: str, model: str):
    """Log AI API request"""
    log_event("AI_REQUEST", {"provider": provider, "model": model})


def log_ai_response(provider: str, success: bool, latency_ms: float = None):
    """Log AI API response"""
    details = {"provider": provider, "success": success}
    if latency_ms:
        details["latency_ms"] = round(latency_ms, 2)
    log_event("AI_RESPONSE", details)


def log_user_action(action: str, target: str = None):
    """Log user interaction"""
    details = {"action": action}
    if target:
        details["target"] = target
    log_event("USER_ACTION", details)


def log_error(error_type: str, message: str, exc_info: bool = False):
    """Log an error with optional traceback"""
    logger.error(f"ERROR [{error_type}]: {message}", exc_info=exc_info)


def log_performance(operation: str, duration_ms: float):
    """Log performance metric"""
    log_event("PERFORMANCE", {"operation": operation, "duration_ms": round(duration_ms, 2)})


# Auto-setup with defaults when imported
if not _logging_configured:
    setup_logging()
