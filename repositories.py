# repositories.py
import logging
import datetime
from dataclasses import dataclass
from typing import Optional, List

from database import Database
from model import Student, Module, Enrollment, Goal, GradeAverageGoal, DeadlineGoal, CpPaceGoal

@dataclass
# Repository for managing Student entities in the database. 
# Provides methods to upsert students, retrieve aggregates, save goals, and list students.
class StudentRepository:
    database: Database

    # Update or insert a student record in the database. This method is 
    # used for both creating new students and updating existing ones.
    def upsert(self, student: Student) -> None:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")

        cursor = self.database.conn.cursor()
        # ON CONFLICT clause ensures that if a student with the same student_id already exists, it will be updated instead of inserted.
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

    # Retrieve a student aggregate by ID, including enrollments and goals. Returns None if not found.
    def get_aggregate_by_id(self, student_id: str) -> Student | None:
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

        # Load enrollments for this student with a JOIN to get module details
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
            module = Module(module_id=str(module_id), title=str(title), ects=int(ects))
            enrollments.append(
                Enrollment(
                    module=module,
                    grade=float(grade) if grade is not None else None,
                    date_passed=datetime.date.fromisoformat(date_passed) if date_passed else None,
                )
            )

        # Load goals from student_goals table
        cursor.execute(
            "SELECT goal_type, value FROM student_goals WHERE student_id=?",
            (student_id,),
        )
        goals: List[Goal] = []
        for goal_type, value in cursor.fetchall():
            if goal_type == "GradeAverageGoal":
                goals.append(GradeAverageGoal(target_avg=float(value)))
            elif goal_type == "CpPaceGoal":
                goals.append(CpPaceGoal(target_cp_per_month=float(value)))
            elif goal_type == "DeadlineGoal":
                goals.append(DeadlineGoal(duration_months=int(value)))

        logging.info("Student aggregate loaded: %s (enrollments=%d, goals=%d)", sid, len(enrollments), len(goals))
        return Student(student_id=sid, name=name, start_date=start_date, enrollments=enrollments, goals=goals)

    # Save Goal objects for a student in the student_goals table. Deletes old goals and inserts new ones.
    def save_goals(self, student_id: str, goals: List[Goal]) -> None:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")

        cursor = self.database.conn.cursor()

        # Delete old goals for this student
        cursor.execute("DELETE FROM student_goals WHERE student_id=?", (student_id,))

        # Save new goals
        for goal in goals:
            goal_type = goal.__class__.__name__
            if isinstance(goal, GradeAverageGoal):
                value = goal.target_avg
            elif isinstance(goal, CpPaceGoal):
                value = goal.target_cp_per_month
            elif isinstance(goal, DeadlineGoal):
                value = goal.duration_months
            else:
                continue

            cursor.execute(
                "INSERT INTO student_goals (student_id, goal_type, value) VALUES (?, ?, ?)",
                (student_id, goal_type, value),
            )

        self.database.conn.commit()
        logging.info(f"Goals for student {student_id} saved: {len(goals)} goals.")

    # List all students in the database, without enrollments or goals. Used for dropdowns or lists.
    def list_all(self) -> List[Student]:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")

        cursor = self.database.conn.cursor()
        cursor.execute(
            "SELECT student_id, name, start_date FROM student ORDER BY name COLLATE NOCASE, student_id"
        )
        out: List[Student] = []
        for student_id, name, start_date_str in cursor.fetchall():
            out.append(Student(str(student_id), str(name), datetime.date.fromisoformat(start_date_str)))
        logging.info("Students listed: %d", len(out))
        return out

    # Close the database connection when the repository is no longer needed. This is important for resource management.
    def close(self) -> None:
        self.database.close()


@dataclass
# Repository for managing Module entities in the database. 
# Provides methods to upsert modules and list them.
class ModuleRepository:
    database: Database

    # Upsert a module record in the database. This method is used for both creating new modules and updating existing ones.
    def upsert(self, module: Module) -> None:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.database.conn.cursor()
        # ON CONFLICT clause ensures that if a module with the same module_id already exists, it will be updated instead of inserted.
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
        
    # Retrieve a module by ID. Returns None if not found.
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

    # List all modules in the database, ordered by title. Used for dropdowns or lists.
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

    # Close the database connection when the repository is no longer needed. This is important for resource management.
    def close(self) -> None:
        self.database.close()


@dataclass
# Repository for managing Enrollment entities in the database. 
# Provides methods to upsert enrollments and list them by student.
class EnrollmentRepository:
    database: Database

    # Upsert an enrollment record in the database. This method is used for both 
    # creating new enrollments and updating existing ones.
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
        # ON CONFLICT clause ensures that if an enrollment with the same student_id and module_id already exists, it will be updated instead of inserted.
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

    # List all enrollments for a specific student. Returns an empty list if none are found.
    def list_by_student(self, student_id: str) -> List[Enrollment]:
        if self.database.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.database.conn.cursor()
        # load enrollments for this student with a JOIN to get module details
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

    # Close the database connection when the repository is no longer needed. This is important for resource management.
    def close(self) -> None:
        self.database.close()
