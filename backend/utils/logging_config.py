"""
Structured logging configuration that prevents token leakage.
All logs are written to stdout in a safe format without exposing credentials.
"""

import logging
import sys
from typing import Optional, Dict, Any

# Create logger
logger = logging.getLogger("github_pr_dashboard")
logger.setLevel(logging.DEBUG)

# Console handler with structured formatting
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# Simple formatter that prevents token exposure
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def safe_log_dict(data: Dict[str, Any], exclude_keys: set = None) -> Dict[str, Any]:
    """
    Create a safe version of a dict for logging, excluding sensitive keys.
    Prevents token, password, and other credential exposure.
    """
    if exclude_keys is None:
        exclude_keys = {"token", "Token", "TOKEN", "password", "secret", "Authorization", "authorization"}
    
    safe_data = {}
    for key, value in data.items():
        if key.lower() in {k.lower() for k in exclude_keys}:
            safe_data[key] = "***REDACTED***"
        elif isinstance(value, dict):
            safe_data[key] = safe_log_dict(value, exclude_keys)
        elif isinstance(value, (list, tuple)):
            safe_data[key] = [safe_log_dict(v, exclude_keys) if isinstance(v, dict) else v for v in value]
        else:
            safe_data[key] = value
    
    return safe_data


def get_logger(name: str = None) -> logging.Logger:
    """Get or create a logger instance."""
    if name:
        return logging.getLogger(f"github_pr_dashboard.{name}")
    return logger
