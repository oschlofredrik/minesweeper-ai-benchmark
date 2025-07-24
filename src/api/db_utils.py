"""Database utilities for handling schema differences."""

from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def safe_getattr(obj, attr, default=None):
    """Safely get an attribute that might not exist."""
    return getattr(obj, attr, default) if hasattr(obj, attr) else default