"""Database utilities for handling schema differences."""

from sqlalchemy import inspect
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def get_existing_columns(db: Session, table_name: str) -> set:
    """Get the list of existing columns for a table."""
    try:
        inspector = inspect(db.bind)
        columns = inspector.get_columns(table_name)
        return {col['name'] for col in columns}
    except Exception as e:
        logger.error(f"Error inspecting table {table_name}: {e}")
        return set()


def safe_getattr(obj, attr, default=None):
    """Safely get an attribute that might not exist."""
    return getattr(obj, attr, default) if hasattr(obj, attr) else default