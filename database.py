# database.py
import sqlite3
import logging
from typing import Optional
from dataclasses import dataclass

@dataclass
class Database:
    db_path: str = "dashboard.db"
    conn: Optional[sqlite3.Connection] = None
    def connect(self) -> None:
        try:
            self.conn = sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}.")
            self.conn = None
            raise
        else:
            logging.info("Database connected successfully.")

    def init_db(self) -> None:
        """Create tables if they don't exist."""
        if self.conn is None:
            raise RuntimeError("Database not connected.")

        cursor = self.conn.cursor()
        # Minimal-Beispiel: du kannst das später an dein Modell anpassen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def close(self) -> None:
        if self.conn is not None:
            try:
                self.conn.close()
            except sqlite3.Error as e:
                logging.error(f"Error closing database: {e}.")
            else:
                self.conn = None
                logging.info("Database connection closed.")
