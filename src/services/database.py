"""Database service for conversation state persistence.

This module provides the DatabaseService singleton for managing
conversation history in a SQLite database.
"""

import logging
import os
import pickle
import sqlite3
from typing import Optional, List, Any, Union

from src.config.settings import DATABASE_PATH
from src.models.conversation import ConversationHistory
from agents import TResponseInputItem

logger = logging.getLogger(__name__)


class DatabaseService:
    """Singleton service for database operations.

    This class provides methods to interact with the SQLite database
    that stores conversation history.
    """

    _instance = None
    _connection: Optional[sqlite3.Connection] = None

    def __new__(cls) -> "DatabaseService":
        """Create or return the singleton instance.

        Returns:
            DatabaseService: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
            cls._instance._initialize_db()
        return cls._instance

    def _initialize_db(self) -> None:
        """Initialize the database connection and create tables if needed."""
        try:
            self._connection = sqlite3.connect(DATABASE_PATH)
            self._connection.execute("PRAGMA journal_mode=WAL")
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys=ON")
            # Create tables if they don't exist
            self._create_tables()
            logger.info(f"Database initialized at {DATABASE_PATH}")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS convos("
                "chat_id INTEGER NOT NULL PRIMARY KEY, "
                "last_agent_name TEXT NOT NULL, "
                "input_list BLOB NOT NULL, "
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) WITHOUT ROWID"
            )
            # Create trigger to update the updated_at timestamp
            self._connection.execute(
                "CREATE TRIGGER IF NOT EXISTS update_convos_timestamp "
                "AFTER UPDATE ON convos "
                "BEGIN "
                "   UPDATE convos SET updated_at = CURRENT_TIMESTAMP WHERE chat_id = NEW.chat_id; "
                "END"
            )
            self._connection.commit()
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise

    def get_conversation_history(self, chat_id: int) -> Optional[ConversationHistory]:
        """Retrieve conversation history for a specific chat.

        Args:
            chat_id: The Telegram chat ID

        Returns:
            Optional[ConversationHistory]: The conversation history or None if not found

        Raises:
            sqlite3.Error: If a database error occurs
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "SELECT input_list, last_agent_name FROM convos WHERE chat_id = ?",
                (chat_id,),
            )
            result = cursor.fetchone()

            if result is None:
                return None

            return ConversationHistory(
                input_list=pickle.loads(result[0]), last_agent_name=result[1]
            )
        except (sqlite3.Error, pickle.PickleError) as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return None

    def save_conversation_history(
        self, chat_id: int, input_list: List[TResponseInputItem], last_agent_name: str
    ) -> bool:
        """Save conversation history for a specific chat.

        Args:
            chat_id: The Telegram chat ID
            input_list: List of conversation inputs
            last_agent_name: Name of the last agent that processed the conversation

        Returns:
            bool: True if successful, False otherwise

        Raises:
            sqlite3.Error: If a database error occurs
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO convos (chat_id, last_agent_name, input_list) VALUES (?, ?, ?)",
                (chat_id, last_agent_name, pickle.dumps(input_list)),
            )
            self._connection.commit()
            return True
        except (sqlite3.Error, pickle.PickleError) as e:
            logger.error(f"Error saving conversation history: {str(e)}")
            return False

    def delete_conversation_history(self, chat_id: int) -> bool:
        """Delete conversation history for a specific chat.

        Args:
            chat_id: The Telegram chat ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._connection.execute("DELETE from convos where chat_id = ?", (chat_id,))
            self._connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting conversation history: {str(e)}")
            return False

    def close(self) -> None:
        """Close the database connection properly."""
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                logger.info("Database connection closed")
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {str(e)}")

    def __del__(self) -> None:
        """Ensure database connection is closed on object destruction."""
        self.close()
