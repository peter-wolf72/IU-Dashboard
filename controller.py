# controller.py
import datetime
from dataclasses import dataclass
from typing import List, Optional

from services import DashboardService
from model import Student, Module, GoalEvaluation

@dataclass
# Controller for the Dashboard application, responsible for handling user interactions 
# and orchestrating between the view and service layers.
class DashboardController:
    dashboard_service: DashboardService

    # Methods to process data from the view and delegate to the service layer
    def process_student_data(self, student: Student) -> None:
        self.dashboard_service.update_student_data(student)

    def process_module_data(self, module: Module) -> None:
        self.dashboard_service.add_module_to_catalogue(module)

    def process_enrollment_data(
        self,
        student: Student,
        module: Module,
        grade: Optional[float] = None,
        date: Optional[datetime.date] = None,
    ) -> None:
        self.dashboard_service.update_study_progress(student.student_id, module.module_id, grade, date)

    def process_goal_data(self, student_id: str, target_duration: int, target_avg: float, target_cp: float) -> None:
        if target_duration <= 0:
            raise ValueError("Dauer in Monaten muss > 0 sein.")
        if target_avg <= 0:
            raise ValueError("Notendurchschnitt muss > 0 sein.")
        if target_cp < 0:
            raise ValueError("Arbeitstempo darf nicht negativ sein.")

        self.dashboard_service.update_student_goals(student_id, target_duration, target_avg, target_cp)

    # Methods to retrieve data for the view
    def refresh_dashboard_stats(self, student: Student) -> List[GoalEvaluation]:
        return self.dashboard_service.evaluate_student_goals(student)

    # Method to gracefully shutdown the application, e.g. close database connections if needed.
    def shutdown(self) -> None:
        self.dashboard_service.close()

    # Additional helper methods to retrieve lists of students for dropdowns or other UI elements.
    def refresh_student_list(self) -> List[Student]:
        return self.dashboard_service.list_students()

    # Additional helper method to retrieve the student aggregate for a given student ID, including enrollments and goals.
    def get_student_aggregate(self, student_id: str) -> Student:
        return self.dashboard_service.get_student_aggregate(student_id)

    # Additional helper method to retrieve the list of modules for module management.
    def refresh_module_list(self) -> List[Module]:
        return self.dashboard_service.list_modules()