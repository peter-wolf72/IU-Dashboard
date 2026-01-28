# services.py
import datetime
from typing import List
from dataclasses import dataclass

from repositories import StudentRepository, ModuleRepository, EnrollmentRepository
from model import Student, StudyProgram, Goal, GoalEvaluation, GradeAverageGoal, DeadlineGoal, CpPaceGoal

@dataclass
class DashboardService:
    student_repository: StudentRepository
    module_repository: ModuleRepository
    enrollment_repository: EnrollmentRepository

    def _months_since(self, start: datetime.date, now: datetime.date | None = None) -> int:
        now = now or datetime.date.today()
        months = (now.year - start.year) * 12 + (now.month - start.month)
        return max(0, months)

    def calc_average_grade(self, student: Student) -> float:
        enrollments = self.enrollment_repository.list_by_student(student.student_id)
        grades = [e.grade for e in enrollments if e.grade is not None]
        if not grades:
            return 0.0
        return sum(grades) / len(grades)

    def calc_time_progress(self, student: Student, program: StudyProgram) -> float:
        months = self._months_since(student.start_date)
        if program.duration_months <= 0:
            return 0.0
        return min(100.0, (months / program.duration_months) * 100.0)

    def calc_earned_ects(self, student: Student) -> int:
        enrollments = self.enrollment_repository.list_by_student(student.student_id)
        earned = 0
        for e in enrollments:
            if e.date_passed is None:
                continue
            mod = self.module_repository.get_by_id(e.module_id)
            if mod is None:
                continue
            earned += mod.ects
        return earned

    def calc_cp_progress(self, student: Student, program: StudyProgram) -> float:
        if program.total_ects <= 0:
            return 0.0
        earned = self.calc_earned_ects(student)
        return min(100.0, (earned / program.total_ects) * 100.0)

    def calc_cp_pace(self, student: Student) -> float:
        months = max(1, self._months_since(student.start_date))
        earned = self.calc_earned_ects(student)
        return earned / months

    def evaluate_goals(self, student: Student, program: StudyProgram, goals: List[Goal]) -> List[GoalEvaluation]:
        return [g.evaluate(student, program, self) for g in goals]

    def default_goals_for(self, program: StudyProgram) -> List[Goal]:
        return [
            GradeAverageGoal(target_avg=2.5),
            CpPaceGoal(target_cp_per_month=5.0),
            DeadlineGoal(duration_months=program.duration_months),
        ]
