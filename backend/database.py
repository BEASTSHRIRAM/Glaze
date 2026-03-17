"""SQLite database management for Glaze."""
import sqlite3
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_PATH = "glaze.db"


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def create_tables():
    """Create database tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create oauth_tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                user_id TEXT PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                expires_in INTEGER,
                token_type TEXT DEFAULT 'Bearer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                link TEXT NOT NULL,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_time TEXT
            )
        """)
        
        # Create indexing_status table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indexing_status (
                file_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                error_message TEXT,
                last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(file_id)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_id ON files(file_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_modified_time ON files(modified_time)
        """)
        
        conn.commit()
        logger.info("Database tables created successfully")


def insert_file_metadata(
    file_id: str,
    file_name: str,
    mime_type: str,
    link: str,
    modified_time: Optional[str] = None
) -> None:
    """Insert or update file metadata."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO files (file_id, file_name, mime_type, link, modified_time, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (file_id, file_name, mime_type, link, modified_time, datetime.now().isoformat()))
        logger.info(f"Inserted/updated metadata for file: {file_id}")


def get_file_metadata(file_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve file metadata by file_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM files WHERE file_id = ?
        """, (file_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_all_files() -> List[Dict[str, Any]]:
    """Retrieve all file metadata."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files ORDER BY indexed_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_indexing_status(
    file_id: str,
    status: str,
    chunk_count: int = 0,
    error_message: Optional[str] = None
) -> None:
    """Update indexing status for a file."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO indexing_status (file_id, status, chunk_count, error_message, last_attempt)
            VALUES (?, ?, ?, ?, ?)
        """, (file_id, status, chunk_count, error_message, datetime.now().isoformat()))
        logger.info(f"Updated indexing status for file {file_id}: {status}")


def get_indexing_status(file_id: str) -> Optional[Dict[str, Any]]:
    """Get indexing status for a file."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM indexing_status WHERE file_id = ?
        """, (file_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def is_file_indexed(file_id: str) -> bool:
    """Check if a file has been indexed."""
    status = get_indexing_status(file_id)
    return status is not None and status['status'] == 'completed'


def initialize_database():
    """Initialize the database with all required tables and indexes."""
    try:
        create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def store_oauth_token(user_id: str, token_data: Dict[str, Any]) -> None:
    """Store OAuth tokens for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO oauth_tokens 
            (user_id, access_token, refresh_token, expires_in, token_type, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            token_data.get("access_token"),
            token_data.get("refresh_token"),
            token_data.get("expires_in"),
            token_data.get("token_type", "Bearer"),
            datetime.now().isoformat()
        ))
        logger.info(f"Stored OAuth tokens for user: {user_id}")


def get_oauth_token(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve OAuth tokens for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT access_token, refresh_token, expires_in, token_type FROM oauth_tokens WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                "access_token": row[0],
                "refresh_token": row[1],
                "expires_in": row[2],
                "token_type": row[3]
            }
        return None


def delete_oauth_token(user_id: str) -> None:
    """Delete OAuth tokens for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM oauth_tokens WHERE user_id = ?
        """, (user_id,))
        logger.info(f"Deleted OAuth tokens for user: {user_id}")
