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
            self.conn.execute("PRAGMA foreign_keys = ON;")
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                program_id TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS module (
                module_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                ects INTEGER NOT NULL CHECK (ects >= 0)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enrollment (
                student_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                grade REAL,
                date_passed TEXT,
                PRIMARY KEY (student_id, module_id),
                FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
                FOREIGN KEY (module_id) REFERENCES module(module_id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_goals (
                student_id TEXT NOT NULL,
                goal_type TEXT NOT NULL,
                value REAL NOT NULL,
                PRIMARY KEY (student_id, goal_type),
                FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
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
