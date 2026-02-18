# services.py
import datetime
from typing import List, Optional
from dataclasses import dataclass, field

from repositories import StudentRepository, ModuleRepository, EnrollmentRepository
from model import (
    Student,
    Module,
    StudyProgram,
    Goal,
    GoalEvaluation,
    GradeAverageGoal,
    DeadlineGoal,
    CpPaceGoal,
)

@dataclass
class DashboardService:
    student_repository: StudentRepository
    module_repository: ModuleRepository
    enrollment_repository: EnrollmentRepository

    # Nicht im UML explizit als Attribut gezeigt, aber notwendig, weil evaluate_student_goals(program) nicht als Param hat.
    _program: StudyProgram = field(default_factory=lambda: StudyProgram(
        program_id="IU-STD",
        name="Studiengang (Default)",
        total_ects=180,
        duration_months=36,
    ))
    _goals: List[Goal] = field(default_factory=lambda: [
        GradeAverageGoal(target_avg=2.5),
        CpPaceGoal(target_cp_per_month=5.0),
        DeadlineGoal(duration_months=36),
    ])

    def update_student_data(self, student: Student) -> None:
        # Command: nur Stammdaten speichern (kein Enrichment)
        self.student_repository.upsert(student)

    def get_student_aggregate(self, student_id: str) -> Student:
        student = self.student_repository.get_aggregate_by_id(student_id)
        if student is None:
            raise ValueError(f"Student not found: {student_id}")
        return student

    def add_module_to_catalogue(self, module: Module) -> None:
        self.module_repository.upsert(module)

    def update_study_progress(
        self,
        student_id: str,
        module_id: str,
        grade: Optional[float],
        date_passed: Optional[datetime.date],
    ) -> None:
        self.enrollment_repository.upsert(student_id, module_id, grade, date_passed)

    def evaluate_student_goals(self, student: Student) -> List[GoalEvaluation]:
        """
        Read: delegiert an das Rich Domain Model (Student.evaluate_all_goals).
        Das Aggregat kennt seine Goals und evaluiert sie selbst.
        """
        # Aggregate mit Goals laden (falls noch nicht geladen)
        aggregate = student if student.goals else self.get_student_aggregate(student.student_id)
        return aggregate.evaluate_all_goals(self._program)

    def close(self) -> None:
        # Lifecycle-Kapselung (Controller kennt nur Service; Shutdown muss irgendwo landen)
        self.enrollment_repository.close()
        self.module_repository.close()
        self.student_repository.close()

    def list_students(self) -> List[Student]:
        return self.student_repository.list_all()

    def list_modules(self) -> List[Module]:
        return self.module_repository.list_all()

    def update_student_goals(self, student_id: str, duration_months: int, target_avg: float, target_cp_per_month: float) -> None:
        """
        Erstellt Goal-Objekte aus den UI-Werten und speichert sie via Repository.
        """
        goals: List[Goal] = [
            GradeAverageGoal(target_avg=target_avg),
            CpPaceGoal(target_cp_per_month=target_cp_per_month),
            DeadlineGoal(duration_months=duration_months),
        ]
        self.student_repository.save_goals(student_id, goals)
