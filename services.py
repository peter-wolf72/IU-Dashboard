# services.py
import datetime
from typing import List, Optional
from dataclasses import dataclass, field
import logging

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
# Service layer for the Dashboard application, responsible for orchestration between repositories and the controller.
class DashboardService:
    student_repository: StudentRepository
    module_repository: ModuleRepository
    enrollment_repository: EnrollmentRepository

    # Default study program configuration, can be extended to support multiple programs in the future.
    def create_default_program() -> StudyProgram:
        logging.info("Default StudyProgram created.")
        return StudyProgram(
            name="Angewandte Künstliche Intelligenz",
            total_ects=180,
            duration_months=48,
    )

    _program: StudyProgram = field(default_factory=create_default_program)

    # Methods to handle business logic for students, modules, enrollments, and goal evaluations.
    def update_student_data(self, student: Student) -> None:
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
        aggregate = student if student.goals else self.get_student_aggregate(student.student_id)
        return aggregate.evaluate_all_goals(self._program)

    def list_students(self) -> List[Student]:
        return self.student_repository.list_all()

    def list_modules(self) -> List[Module]:
        return self.module_repository.list_all()

    def update_student_goals(self, student_id: str, duration_months: int, target_avg: float, target_cp_per_month: float) -> None:
        goals: List[Goal] = [
            GradeAverageGoal(target_avg=target_avg),
            CpPaceGoal(target_cp_per_month=target_cp_per_month),
            DeadlineGoal(duration_months=duration_months),
        ]
        self.student_repository.save_goals(student_id, goals)

    def close(self) -> None:
        self.enrollment_repository.close()
        self.module_repository.close()
        self.student_repository.close()
