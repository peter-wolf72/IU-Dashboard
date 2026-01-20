# controller.py
import datetime
from typing import Dict, Any

from services import DashboardService
from model import Student
from database import Database

class DashboardController:
    def __init__(self, service: DashboardService, db: Database) -> None:
        self.service = service
        self.db = db  # für close()

    def save_student(self, student_id: str, name: str, start_date: datetime.date) -> None:
        student = Student(student_id, name, start_date)
        # Service könnte das auch übernehmen – aber im Prototyp ist das ok:
        self.service.student_repo.upsert(student)

    def get_overview(self, student_id: str) -> Dict[str, Any]:
        return self.service.get_overview(student_id)

    def shutdown(self) -> None:
        self.db.close()
