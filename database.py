"""
Database - Database operations (Backwards Compatibility Wrapper)

This module provides backwards compatibility for code importing from database.py.
The actual implementation has moved to app/database.py.
"""

# Re-export everything from app.database for backwards compatibility
from app.database import (
    DB_PATH,
    init_db,
    get_db,
    close_db,
    run_migrations,
)

__all__ = ['DB_PATH', 'init_db', 'get_db', 'close_db', 'run_migrations']
