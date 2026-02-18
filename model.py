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

    # Calculated properties and methods for goal evaluation
    def _months_since_start(self, now: Optional[datetime.date] = None) -> int:
        """
        Calculate the number of months since the student started.

        :param self: The student instance.
        :param now: The current date. Defaults to today if not provided.
        :type now: Optional[datetime.date]
        :return: The number of months since the start date.
        :rtype: int
        """
        now = now or datetime.date.today()
        months = (now.year - self.start_date.year) * 12 + (now.month - self.start_date.month)
        return max(0, months)

    def get_average_grade(self) -> float:
        """
        Calculate the average grade of the student.

        :param self: The student instance.
        :return: The average grade of the student.
        :rtype: float
        """
        grades = [e.grade for e in self.enrollments if e.grade is not None]
        return (sum(grades) / len(grades)) if grades else 0.0

    def get_time_progress_percentage(self, duration_months: int) -> float:
        """
        Calculate the percentage of time progress based on the program duration.

        :param self: The student instance.
        :param duration_months: The total duration of the program in months.
        :type duration_months: int
        :return: The percentage of time progress based on the duration.
        :rtype: float
        """
        if duration_months <= 0:
            return 0.0
        months = self._months_since_start()
        return min(100.0, (months / duration_months) * 100.0)

    def get_earned_ects(self) -> int:
        """
        Calculate the total earned ECTS credits for the student.

        :param self: The student instance.
        :return: The total earned ECTS credits.
        :rtype: int
        """
        return sum(e.module.ects for e in self.enrollments if e.date_passed is not None)

    def get_cp_progress_percentage(self, total_ects: int) -> float:
        """
        Calculate the percentage of completed ECTS credits based on the total program credits.

        :param self: The student instance.
        :param total_ects: The total ECTS credits of the program.
        :type total_ects: int
        :return: The percentage of completed ECTS credits.
        :rtype: float
        """
        if total_ects <= 0:
            return 0.0
        return min(100.0, (self.get_earned_ects() / total_ects) * 100.0)

    def get_cp_per_month(self) -> float:
        """
        Calculate the average ECTS credits earned per month.

        :param self: The student instance.
        :return: The average ECTS credits earned per month.
        :rtype: float
        """
        months = max(1, self._months_since_start())
        return self.get_earned_ects() / months

    def evaluate_all_goals(self, program: StudyProgram) -> list["GoalEvaluation"]:
        """
        Evaluate all goals for the student against the given study program.

        :param self: The student instance.
        :param program: The study program instance.
        :type program: StudyProgram
        :return: A list of goal evaluations for the student.
        :rtype: list[GoalEvaluation]
        """
        return [goal.evaluate(self, program) for goal in self.goals]

# Goal evaluation data models
@dataclass(frozen=True)
class EvaluationCriterion:
    name: str
    value: float
    target: float

# Goal evaluation result data model
@dataclass(frozen=True)
class GoalEvaluation:
    status: Status
    criteria: list[EvaluationCriterion]

# Abstract base class for goals
class Goal(ABC):
    @abstractmethod
    def evaluate(self, student: Student, program: StudyProgram) -> GoalEvaluation:
        raise NotImplementedError

    @abstractmethod
    def get_title(self) -> str:
        raise NotImplementedError

# Concrete goal implementations

# GradeAverageGoal implementation
@dataclass(frozen=True)
class GradeAverageGoal(Goal):
    target_avg: float

    def get_title(self) -> str:
        return "Notenschnitt"

    def evaluate(self, student: Student, program: StudyProgram) -> GoalEvaluation:
        """
        Evaluate the goal for the student against the given study program.
        
        :param self: The goal instance.
        :param student: The student instance.
        :type student: Student
        :param program: The study program instance.
        :type program: StudyProgram
        :return: The goal evaluation for the student.
        :rtype: GoalEvaluation
        """
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

# DeadlineGoal implementation
@dataclass(frozen=True)
class DeadlineGoal(Goal):
    duration_months: int

    def get_title(self) -> str:
        return "Deadline / Plan"

    def evaluate(self, student: Student, program: StudyProgram) -> GoalEvaluation:
        """
        Evaluate the goal for the student against the given study program.
        
        :param self: The goal instance.
        :param student: The student instance.
        :type student: Student
        :param program: The study program instance.
        :type program: StudyProgram
        :return: The goal evaluation for the student.
        :rtype: GoalEvaluation
        """
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
# CpPaceGoal implementation
@dataclass(frozen=True)
class CpPaceGoal(Goal):
    target_cp_per_month: float

    def get_title(self) -> str:
        return "CP Pace"

    def evaluate(self, student: Student, program: StudyProgram) -> GoalEvaluation:
        """
        Evaluate the goal for the student against the given study program.
        
        :param self: The goal instance.
        :param student: The student instance.
        :type student: Student
        :param program: The study program instance.
        :type program: StudyProgram
        :return: The goal evaluation for the student.
        :rtype: GoalEvaluation
        """
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
