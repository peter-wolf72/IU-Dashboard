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
        # Read: stets auf vollständigem Aggregate evaluieren (ohne student zu mutieren)
        aggregate = student if student.enrollments else self.get_student_aggregate(student.student_id)
        return [g.evaluate(aggregate, self._program) for g in self._goals]

    def close(self) -> None:
        # Lifecycle-Kapselung (Controller kennt nur Service; Shutdown muss irgendwo landen)
        self.enrollment_repository.close()
        self.module_repository.close()
        self.student_repository.close()

    def list_students(self) -> List[Student]:
        return self.student_repository.list_all()

    def list_modules(self) -> List[Module]:
        return self.module_repository.list_all()
