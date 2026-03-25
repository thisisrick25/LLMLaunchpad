"""Database setup and management for LLMLaunchpad."""

import sqlite3
from pathlib import Path
from typing import Optional

from .config import get_config


def get_db_path() -> Path:
    """Get the database file path."""
    config = get_config()
    return Path(config.data_dir) / "chats.db"


def init_db() -> None:
    """Initialize the database with required tables."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    """)
    
    # Full-text search virtual table
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
            content,
            content=messages,
            content_rowid=rowid
        )
    """)
    
    # Indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conversation 
        ON messages(conversation_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_updated 
        ON conversations(updated_at DESC)
    """)
    
    conn.commit()
    conn.close()


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
