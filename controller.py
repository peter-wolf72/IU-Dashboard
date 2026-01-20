# controller.py
import datetime
from typing import Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from services import DashboardService
from model import Student
from database import Database

@dataclass
class DashboardController:
    service: DashboardService
    db: Database

    def save_student(self, student_id: str, name: str, start_date: datetime.date) -> None:
        student = Student(student_id, name, start_date)
        # Service könnte das auch übernehmen – aber im Prototyp ist das ok:
        self.service.student_repo.upsert(student)

    def get_overview(self, student_id: str) -> Dict[str, Any]:
        return self.service.get_overview(student_id)

    def shutdown(self) -> None:
        self.db.close()
