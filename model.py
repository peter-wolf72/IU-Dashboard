# model.py
# Data model definitions for the Dashboard application.

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# Status enum for goal evaluations
class Status(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"

# Module data model
@dataclass(frozen=True)
class Module:
    module_id: str
    title: str
    ects: int

# Study program data model
@dataclass(frozen=True)
class StudyProgram:
    program_id: str
    name: str
    total_ects: int
    duration_months: int

# Enrollment data model
@dataclass(frozen=True)
class Enrollment:
    # UML: Enrollment hat grade/date_passed als Attribute; die Beziehung zu Module ist eine Assoziation.
    module: Module
    grade: Optional[float] = None
    date_passed: Optional[datetime.date] = None

# Student data model
@dataclass
class Student:
    student_id: str
    name: str
    start_date: datetime.date
    enrollments: list[Enrollment] = field(default_factory=list)
    goals: list["Goal"] = field(default_factory=list)

    def _months_since_start(self, now: Optional[datetime.date] = None) -> int:
        now = now or datetime.date.today()
        months = (now.year - self.start_date.year) * 12 + (now.month - self.start_date.month)
        return max(0, months)

    def get_average_grade(self) -> float:
        grades = [e.grade for e in self.enrollments if e.grade is not None]
        return (sum(grades) / len(grades)) if grades else 0.0

    def get_time_progress_percentage(self, duration_months: int) -> float:
        if duration_months <= 0:
            return 0.0
        months = self._months_since_start()
        return min(100.0, (months / duration_months) * 100.0)

    def get_earned_ects(self) -> int:
        return sum(e.module.ects for e in self.enrollments if e.date_passed is not None)

    def get_cp_progress_percentage(self, total_ects: int) -> float:
        if total_ects <= 0:
            return 0.0
        return min(100.0, (self.get_earned_ects() / total_ects) * 100.0)

    def get_cp_per_month(self) -> float:
        months = max(1, self._months_since_start())
        return self.get_earned_ects() / months

    def evaluate_all_goals(self, program: StudyProgram) -> list["GoalEvaluation"]:
        """
        Rich Domain Model: zentraler Evaluierungspunkt.
        Evaluiert alle Goals des Students gegen das Programm.
        """
        return [goal.evaluate(self, program) for goal in self.goals]

@dataclass(frozen=True)
class EvaluationCriterion:
    name: str
    value: float
    target: float

@dataclass(frozen=True)
class GoalEvaluation:
    status: Status
    criteria: list[EvaluationCriterion]

class Goal(ABC):
    @abstractmethod
    def evaluate(self, student: Student, program: StudyProgram) -> GoalEvaluation:
        raise NotImplementedError

    @abstractmethod
    def get_title(self) -> str:
        raise NotImplementedError

@dataclass(frozen=True)
class GradeAverageGoal(Goal):
    target_avg: float

    def get_title(self) -> str:
        return "Notenschnitt"

    def evaluate(self, student: Student, program: StudyProgram) -> GoalEvaluation:
        avg = student.get_average_grade()
        if avg <= self.target_avg:
            status = Status.GREEN
        elif avg <= self.target_avg + 0.3:
            status = Status.YELLOW
        else:
            status = Status.RED

        return GoalEvaluation(
            status=status,
            criteria=[
                EvaluationCriterion(name=f"{self.get_title()} – Ø Note", value=avg, target=self.target_avg),
            ],
        )

@dataclass(frozen=True)
class DeadlineGoal(Goal):
    duration_months: int

    def get_title(self) -> str:
        return "Deadline / Plan"

    def evaluate(self, student: Student, program: StudyProgram) -> GoalEvaluation:
        time_pct = student.get_time_progress_percentage(self.duration_months)
        cp_pct = student.get_cp_progress_percentage(program.total_ects)
        delta = cp_pct - time_pct

        if delta >= 0:
            status = Status.GREEN
        elif delta >= -10:
            status = Status.YELLOW
        else:
            status = Status.RED

        return GoalEvaluation(
            status=status,
            criteria=[
                EvaluationCriterion(name=f"{self.get_title()} – CP%", value=cp_pct, target=time_pct),
                EvaluationCriterion(name=f"{self.get_title()} – Delta(CP%-Time%)", value=delta, target=0.0),
            ],
        )

@dataclass(frozen=True)
class CpPaceGoal(Goal):
    target_cp_per_month: float

    def get_title(self) -> str:
        return "CP Pace"

    def evaluate(self, student: Student, program: StudyProgram) -> GoalEvaluation:
        pace = student.get_cp_per_month()
        if pace >= self.target_cp_per_month:
            status = Status.GREEN
        elif pace >= self.target_cp_per_month * 0.8:
            status = Status.YELLOW
        else:
            status = Status.RED

        return GoalEvaluation(
            status=status,
            criteria=[
                EvaluationCriterion(name=f"{self.get_title()} – CP/Monat", value=pace, target=self.target_cp_per_month),
            ],
        )
