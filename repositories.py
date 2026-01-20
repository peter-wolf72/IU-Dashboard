# repositories.py
import logging
from typing import Optional
import datetime

from database import Database
from model import Student

class StudentRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def upsert(self, student: Student) -> None:
        """Insert oder Update (für Prototyp angenehm)."""
        if self.db.conn is None:
            raise RuntimeError("Database not connected")

        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO student (student_id, name, start_date)
            VALUES (?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
              name=excluded.name,
              start_date=excluded.start_date
            """,
            (student.student_id, student.name, student.start_date.isoformat())
        )
        self.db.conn.commit()
        logging.info("Student saved: %s", student.student_id)

    def get_by_id(self, student_id: str) -> Optional[Student]:
        if self.db.conn is None:
            raise RuntimeError("Database not connected")

        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT student_id, name, start_date FROM student WHERE student_id=?",
            (student_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None

        sid, name, start_date_str = row
        start_date = datetime.date.fromisoformat(start_date_str)
        return Student(sid, name, start_date)
