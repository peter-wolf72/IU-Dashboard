# repositories.py
import logging
import datetime
from dataclasses import dataclass
from typing import Optional, List

from database import Database
from model import Student, Module, Enrollment

@dataclass
class StudentRepository:
    database: Database

    def add(self, student: Student) -> None:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.database.conn.cursor()
        cursor.execute(
            "INSERT INTO student (student_id, name, start_date, program_id) VALUES (?, ?, ?, ?)",
            (student.student_id, student.name, student.start_date.isoformat(), student.program_id),
        )
        self.database.conn.commit()

    def update(self, student: Student) -> None:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.database.conn.cursor()
        cursor.execute(
            "UPDATE student SET name=?, start_date=?, program_id=? WHERE student_id=?",
            (student.name, student.start_date.isoformat(), student.program_id, student.student_id),
        )
        self.database.conn.commit()

    def upsert(self, student: Student) -> None:
        """Insert oder Update (für Prototyp angenehm)."""
        if self.database.conn is None:
            raise RuntimeError("Database not connected")

        cursor = self.database.conn.cursor()
        cursor.execute(
            """
            INSERT INTO student (student_id, name, start_date, program_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
              name=excluded.name,
              start_date=excluded.start_date,
              program_id=excluded.program_id
            """,
            (student.student_id, student.name, student.start_date.isoformat(), student.program_id),
        )
        self.database.conn.commit()
        logging.info("Student saved: %s", student.student_id)

    def get_by_id(self, student_id: str) -> Student | None:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")

        cursor = self.database.conn.cursor()
        cursor.execute(
            "SELECT student_id, name, start_date, program_id FROM student WHERE student_id=?",
            (student_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        sid, name, start_date_str, program_id = row
        start_date = datetime.date.fromisoformat(start_date_str)
        return Student(sid, name, start_date, program_id=program_id)

    def close(self) -> None:
        self.database.close()


@dataclass
class ModuleRepository:
    database: Database

    def add(self, module: Module) -> None:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.database.conn.cursor()
        cursor.execute(
            """
            INSERT INTO module (module_id, title, ects)
            VALUES (?, ?, ?)
            ON CONFLICT(module_id) DO UPDATE SET
              title=excluded.title,
              ects=excluded.ects
            """,
            (module.module_id, module.title, module.ects),
        )
        self.database.conn.commit()

    def get_by_id(self, module_id: str) -> Module | None:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.database.conn.cursor()
        cursor.execute("SELECT module_id, title, ects FROM module WHERE module_id=?", (module_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        mid, title, ects = row
        return Module(mid, title, int(ects))

    def close(self) -> None:
        self.database.close()


@dataclass
class EnrollmentRepository:
    database: Database

    def upsert(self, student_id: str, module_id: str, grade: Optional[float], date_passed: Optional[datetime.date]) -> None:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.database.conn.cursor()
        cursor.execute(
            """
            INSERT INTO enrollment (student_id, module_id, grade, date_passed)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(student_id, module_id) DO UPDATE SET
              grade=excluded.grade,
              date_passed=excluded.date_passed
            """,
            (
                student_id,
                module_id,
                grade,
                date_passed.isoformat() if date_passed else None,
            ),
        )
        self.database.conn.commit()

    def list_by_student(self, student_id: str) -> List[Enrollment]:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.database.conn.cursor()
        cursor.execute(
            "SELECT student_id, module_id, grade, date_passed FROM enrollment WHERE student_id=?",
            (student_id,),
        )
        out: List[Enrollment] = []
        for sid, mid, grade, date_passed in cursor.fetchall():
            out.append(
                Enrollment(
                    student_id=sid,
                    module_id=mid,
                    grade=float(grade) if grade is not None else None,
                    date_passed=datetime.date.fromisoformat(date_passed) if date_passed else None,
                )
            )
        return out

    def close(self) -> None:
        self.database.close()
