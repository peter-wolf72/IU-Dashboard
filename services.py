# services.py
from typing import Dict, Any
from repositories import StudentRepository
from dataclasses import dataclass

@dataclass
class DashboardService:
    student_repo: StudentRepository

    def get_overview(self, student_id: str) -> Dict[str, Any]:
        """
        Delivers an overview for the given student.
        """
        student = self.student_repo.get_by_id(student_id)
        if student is None:
            return {"error": "Student not found"}

        # Placeholder: later real logic (Modules/Enrollment)
        avg = student.get_average_grade()
        pace = student.get_cp_per_month()

        # Returns a simple overview dictionary. Change to GoalEvaluation and dataclasses later.
        return {
            "student_name": student.name,
            "average_grade": avg,
            "cp_per_month": pace,
        }
