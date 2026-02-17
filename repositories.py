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

    def upsert(self, student: Student) -> None:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")

        cursor = self.database.conn.cursor()
        cursor.execute(
            """
            INSERT INTO student (student_id, name, start_date)
            VALUES (?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
              name=excluded.name,
              start_date=excluded.start_date
            """,
            (student.student_id, student.name, student.start_date.isoformat()),
        )
        self.database.conn.commit()
        logging.info(f"Student {student.student_id} upserted successfully.")

    def get_aggregate_by_id(self, student_id: str) -> Student | None:
        """
        UML: liefert das Student-Aggregat inkl. Enrollment[*] (read model).
        """
        if self.database.conn is None:
            raise RuntimeError("Database not connected")

        cursor = self.database.conn.cursor()
        cursor.execute(
            "SELECT student_id, name, start_date FROM student WHERE student_id=?",
            (student_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        sid, name, start_date_str = row
        start_date = datetime.date.fromisoformat(start_date_str)

        cursor.execute(
            """
            SELECT
              m.module_id, m.title, m.ects,
              e.grade, e.date_passed
            FROM enrollment e
            JOIN module m ON m.module_id = e.module_id
            WHERE e.student_id=?
            """,
            (student_id,),
        )
        enrollments: List[Enrollment] = []
        for module_id, title, ects, grade, date_passed in cursor.fetchall():
            mod = Module(module_id=str(module_id), title=str(title), ects=int(ects))
            enrollments.append(
                Enrollment(
                    module=mod,
                    grade=float(grade) if grade is not None else None,
                    date_passed=datetime.date.fromisoformat(date_passed) if date_passed else None,
                )
            )

        logging.info("Student aggregate loaded: %s (enrollments=%d)", sid, len(enrollments))
        return Student(student_id=sid, name=name, start_date=start_date, enrollments=enrollments)

    def list_all(self) -> List[Student]:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")

        cursor = self.database.conn.cursor()
        cursor.execute(
            "SELECT student_id, name, start_date FROM student ORDER BY name COLLATE NOCASE, student_id"
        )
        out: List[Student] = []
        for sid, name, start_date_str in cursor.fetchall():
            out.append(Student(str(sid), str(name), datetime.date.fromisoformat(start_date_str)))
        logging.info("Students listed: %d", len(out))
        return out

    def close(self) -> None:
        self.database.close()


@dataclass
class ModuleRepository:
    database: Database

    def upsert(self, module: Module) -> None:
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
        logging.info(f"Module {module.module_id} upserted successfully.")
        
    # Kompatibilität: falls noch Alt-Code .add() aufruft
    def add(self, module: Module) -> None:
        self.upsert(module)

    def get_by_id(self, module_id: str) -> Module | None:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.database.conn.cursor()
        cursor.execute("SELECT module_id, title, ects FROM module WHERE module_id=?", (module_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        mid, title, ects = row
        logging.info(f"Module {mid} retrieved successfully.")
        return Module(mid, title, int(ects))

    def list_all(self) -> List[Module]:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.database.conn.cursor()
        cursor.execute(
            "SELECT module_id, title, ects FROM module ORDER BY title COLLATE NOCASE, module_id"
        )
        out: List[Module] = []
        for mid, title, ects in cursor.fetchall():
            out.append(Module(str(mid), str(title), int(ects)))
        logging.info("Modules listed: %d", len(out))
        return out

    def close(self) -> None:
        self.database.close()


@dataclass
class EnrollmentRepository:
    database: Database

    def upsert(
        self,
        student_id: str,
        module_id: str,
        grade: Optional[float],
        date_passed: Optional[datetime.date],
    ) -> None:
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
        logging.info(f"Enrollment for student {student_id} in module {module_id} upserted successfully.")   
    def list_by_student(self, student_id: str) -> List[Enrollment]:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.database.conn.cursor()
        cursor.execute(
            """
            SELECT
              m.module_id, m.title, m.ects,
              e.grade, e.date_passed
            FROM enrollment e
            JOIN module m ON m.module_id = e.module_id
            WHERE e.student_id=?
            """,
            (student_id,),
        )
        out: List[Enrollment] = []
        for module_id, title, ects, grade, date_passed in cursor.fetchall():
            mod = Module(module_id=str(module_id), title=str(title), ects=int(ects))
            out.append(
                Enrollment(
                    module=mod,
                    grade=float(grade) if grade is not None else None,
                    date_passed=datetime.date.fromisoformat(date_passed) if date_passed else None,
                )
            )
        logging.info(f"Enrollments for student {student_id} retrieved successfully.")
        return out

    def close(self) -> None:
        self.database.close()
