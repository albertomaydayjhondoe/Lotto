"""
Core Logging Module
Provides structured logging utilities for the orchestrator
"""
import logging
import sys
from typing import Any, Dict, Optional


def get_logger(name: str) -> logging.Logger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__ from calling module)
        
    Returns:
        Configured logger instance with structured formatting
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Create structured formatter
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging.
    
    Format: [LEVEL] [module] message | extra={...}
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured output."""
        # Get level name
        level = record.levelname
        
        # Get module name
        module = record.name
        
        # Get message
        message = record.getMessage()
        
        # Build base format
        formatted = f"[{level}] [{module}] {message}"
        
        # Add extra fields if present
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            extra_str = ", ".join(f"{k}={v}" for k, v in extra_fields.items())
            formatted += f" | extra={{{extra_str}}}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        
        return formatted
    
    def _get_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract extra fields from log record."""
        # Standard fields to exclude
        standard_fields = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'pathname', 'process', 'processName', 'relativeCreated',
            'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info'
        }
        
        # Get custom fields
        extra = {}
        for key, value in record.__dict__.items():
            if key not in standard_fields:
                extra[key] = value
        
        return extra


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **kwargs: Any
) -> None:
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance
        level: Log level ('info', 'warning', 'error', 'debug')
        message: Log message
        **kwargs: Additional context fields
    """
    log_func = getattr(logger, level.lower())
    log_func(message, extra=kwargs)
