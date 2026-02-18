# controller.py
import datetime
from dataclasses import dataclass
from typing import List, Optional

from services import DashboardService
from model import Student, Module, GoalEvaluation

@dataclass
class DashboardController:
    service: DashboardService

    def load_initial_data(self) -> None:
        # Seed-Beispiele (kann später durch DB-Skript ersetzt werden)
        self.service.add_module_to_catalogue(Module(module_id="M101", title="Beispielmodul 1", ects=5))
        self.service.add_module_to_catalogue(Module(module_id="M102", title="Beispielmodul 2", ects=5))

    def process_student_data(self, student: Student) -> None:
        self.service.update_student_data(student)

    def process_module_data(self, module: Module) -> None:
        self.service.add_module_to_catalogue(module)

    def process_enrollment_data(
        self,
        student: Student,
        module: Module,
        grade: Optional[float] = None,
        date: Optional[datetime.date] = None,
    ) -> None:
        self.service.update_study_progress(student.student_id, module.module_id, grade, date)

    def process_goal_data(self, student_id: str, target_duration: int, target_avg: float, target_cp: float) -> None:
        """
        Validiert Goal-Daten und delegiert an Service.
        """
        # Grobe Validierung
        if target_duration <= 0:
            raise ValueError("Dauer in Monaten muss > 0 sein.")
        if target_avg <= 0:
            raise ValueError("Notendurchschnitt muss > 0 sein.")
        if target_cp < 0:
            raise ValueError("Arbeitstempo darf nicht negativ sein.")

        self.service.update_student_goals(student_id, target_duration, target_avg, target_cp)

    def refresh_dashboard_stats(self, student: Student) -> List[GoalEvaluation]:
        self.service.update_student_data(student)
        return self.service.evaluate_student_goals(student)

    def shutdown(self) -> None:
        self.service.close()

    def refresh_student_list(self) -> List[Student]:
        return self.service.list_students()

    def get_student_aggregate(self, student_id: str) -> Student:
        return self.service.get_student_aggregate(student_id)

    def refresh_module_list(self) -> List[Module]:
        return self.service.list_modules()