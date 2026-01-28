# model.py
# Data model definitions for the Dashboard application.

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
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
    student_id: str
    module_id: str
    grade: Optional[float] = None
    date_passed: Optional[datetime.date] = None

# Student data model
@dataclass(frozen=True)
class Student:
    student_id: str
    name: str
    start_date: datetime.date
    # program_id ist bewusst ein Identifier (FK) und kein StudyProgram-Objekt:
    # - referenziert StudyProgram.program_id
    # - vermeidet, dass beim Laden eines Student automatisch ein StudyProgram mitgeladen werden muss
    program_id: Optional[str] = None

    # Achtung: "get_*" ist hier semantisch KEIN trivialer Getter,
    # sondern meint fachliche, abgeleitete Kennzahlen (Berechnungen).
    # In dieser Architektur liegen diese Berechnungen im DashboardService,
    # weil dafür Enrollments/Module (Repos/DB) benötigt werden.
    def get_average_grade(self) -> float:
        raise NotImplementedError("Use DashboardService.calc_average_grade(student)")

    def get_time_progress_percentage(self, duration_months: int) -> float:
        raise NotImplementedError("Use DashboardService.calc_time_progress(student, program)")

    def get_cp_progress_percentage(self, total_ects: int) -> float:
        raise NotImplementedError("Use DashboardService.calc_cp_progress(student, program)")

    def get_earned_ects(self) -> int:
        raise NotImplementedError("Use DashboardService.calc_earned_ects(student)")

    def get_cp_per_month(self) -> float:
        raise NotImplementedError("Use DashboardService.calc_cp_pace(student)")


@dataclass(frozen=True)
class GoalEvaluation:
    status: Status
    value: float
    target: float
    value2: float = 0.0
    target2: float = 0.0
    label1: str = ""
    label2: str = ""
    title: str = ""


class Goal(ABC):
    @abstractmethod
    def evaluate(self, student: Student, program: StudyProgram, service: "DashboardService") -> GoalEvaluation:
        raise NotImplementedError

    @abstractmethod
    def get_title(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class GradeAverageGoal(Goal):
    target_avg: float

    def get_title(self) -> str:
        return "Notenschnitt"

    def evaluate(self, student: Student, program: StudyProgram, service: "DashboardService") -> GoalEvaluation:
        avg = service.calc_average_grade(student)
        # kleiner = besser; gelb/rot heuristisch
        if avg <= self.target_avg:
            status = Status.GREEN
        elif avg <= self.target_avg + 0.3:
            status = Status.YELLOW
        else:
            status = Status.RED
        return GoalEvaluation(
            status=status,
            value=avg,
            target=self.target_avg,
            label1="Ø Note",
            label2="Ziel",
            title=self.get_title(),
        )


@dataclass(frozen=True)
class DeadlineGoal(Goal):
    duration_months: int

    def get_title(self) -> str:
        return "Deadline / Plan"

    def evaluate(self, student: Student, program: StudyProgram, service: "DashboardService") -> GoalEvaluation:
        time_pct = service.calc_time_progress(student, program)
        cp_pct = service.calc_cp_progress(student, program)

        # Erwartung: CP% sollte ungefähr Time% halten (mit Toleranz)
        delta = cp_pct - time_pct
        if delta >= 0:
            status = Status.GREEN
        elif delta >= -10:
            status = Status.YELLOW
        else:
            status = Status.RED

        return GoalEvaluation(
            status=status,
            value=cp_pct,
            target=time_pct,
            value2=delta,
            target2=0.0,
            label1="CP%",
            label2="Time%",
            title=self.get_title(),
        )


@dataclass(frozen=True)
class CpPaceGoal(Goal):
    target_cp_per_month: float

    def get_title(self) -> str:
        return "CP Pace"

    def evaluate(self, student: Student, program: StudyProgram, service: "DashboardService") -> GoalEvaluation:
        pace = service.calc_cp_pace(student)
        if pace >= self.target_cp_per_month:
            status = Status.GREEN
        elif pace >= self.target_cp_per_month * 0.8:
            status = Status.YELLOW
        else:
            status = Status.RED

        return GoalEvaluation(
            status=status,
            value=pace,
            target=self.target_cp_per_month,
            label1="CP/Monat",
            label2="Ziel",
            title=self.get_title(),
        )
