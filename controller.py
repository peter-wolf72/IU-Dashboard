# controller.py
import datetime
from dataclasses import dataclass, replace
from typing import List, Optional

from services import DashboardService
from model import Student, StudyProgram, GoalEvaluation, Module
from repositories import StudentRepository, ModuleRepository, EnrollmentRepository

@dataclass
class DashboardController:
    service: DashboardService
    student_repository: StudentRepository
    module_repository: ModuleRepository
    enrollment_repository: EnrollmentRepository

    # minimaler Program-Kontext (kann später via Repository kommen)
    program: StudyProgram = StudyProgram(
        program_id="IU-STD",
        name="Studiengang (Default)",
        total_ects=180,
        duration_months=36,
    )

    def load_initial_data(self) -> None:
        # Seed-Beispiele (idempotent via upsert in ModuleRepository.add)
        self.module_repository.add(Module(module_id="M101", title="Beispielmodul 1", ects=5))
        self.module_repository.add(Module(module_id="M102", title="Beispielmodul 2", ects=5))

    def save_student(self, student: Student) -> None:
        # Konsistenzregel: Student gehört zum im Controller aktiven StudyProgram.
        if student.program_id != self.program.program_id:
            student = replace(student, program_id=self.program.program_id)
        self.student_repository.upsert(student)
    def compute_overview(self, student_id: str) -> List[GoalEvaluation]:
        student = self.student_repository.get_by_id(student_id)
        if student is None:
            return []
        goals = self.service.default_goals_for(self.program)
        return self.service.evaluate_goals(student, self.program, goals)

    def add_or_update_enrollment(
        self,
        student_id: str,
        module_id: str,
        grade: Optional[float],
        date_passed: Optional[datetime.date],
    ) -> None:
        self.enrollment_repository.upsert(student_id, module_id, grade, date_passed)

    def shutdown(self) -> None:
        # Controller bleibt DB-agnostisch; Repos kapseln die DB.
        self.enrollment_repository.close()
        self.module_repository.close()
        self.student_repository.close()