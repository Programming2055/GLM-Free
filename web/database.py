"""SQLite database models for chat history."""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import json

DATABASE_PATH = "chat_history.db"


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database with tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT CHECK(role IN ('user', 'assistant', 'system')),
            content TEXT,
            image_url TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    """)

    # Index for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conversation
        ON messages(conversation_id)
    """)

    conn.commit()
    conn.close()


class Conversation:
    """Conversation model."""

    def __init__(self, id: str, title: str, created_at: str, updated_at: str):
        self.id = id
        self.title = title
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(title: str = "New Chat") -> str:
        """Create a new conversation and return its ID."""
        conn = get_db_connection()
        cursor = conn.cursor()

        conv_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO conversations (id, title) VALUES (?, ?)",
            (conv_id, title)
        )
        conn.commit()
        conn.close()
        return conv_id

    @staticmethod
    def get(conversation_id: str) -> Optional[Dict]:
        """Get a conversation by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    @staticmethod
    def get_all() -> List[Dict]:
        """Get all conversations ordered by updated time."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    @staticmethod
    def update_title(conversation_id: str, title: str):
        """Update conversation title."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, conversation_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def delete(conversation_id: str):
        """Delete a conversation and its messages."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update_timestamp(conversation_id: str):
        """Update the updated_at timestamp."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,)
        )
        conn.commit()
        conn.close()


class Message:
    """Message model."""

    @staticmethod
    def create(
        conversation_id: str,
        role: str,
        content: str,
        image_url: Optional[str] = None
    ) -> str:
        """Create a new message and return its ID."""
        conn = get_db_connection()
        cursor = conn.cursor()

        message_id = str(uuid.uuid4())
        cursor.execute(
            """INSERT INTO messages (id, conversation_id, role, content, image_url)
               VALUES (?, ?, ?, ?, ?)""",
            (message_id, conversation_id, role, content, image_url)
        )
        conn.commit()
        conn.close()

        # Update conversation timestamp
        Conversation.update_timestamp(conversation_id)

        return message_id

    @staticmethod
    def get_by_conversation(conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT * FROM messages
               WHERE conversation_id = ?
               ORDER BY timestamp ASC""",
            (conversation_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    @staticmethod
    def delete(message_id: str):
        """Delete a message."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM messages WHERE id = ?",
            (message_id,)
        )
        conn.commit()
        conn.close()


# Initialize database on module load
init_database()
