# model.py
import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass(frozen=True)
class Student:
    student_id: str
    name: str
    start_date: datetime.date
    
    def get_average_grade(self) -> float:
        # Placeholder implementation
        return 2.0
    
    def get_time_progress_percentage(self, duration_months: int) -> float:
        # Placeholder implementation
        return 50.0
    
    def get_cp_progress_percentage(self, total_ects: int) -> float:
        # Placeholder implementation
        return 30.0
    
    def get_earned_ects(self) -> int:
        # Placeholder implementation
        return 15
    
    def get_cp_per_month(self) -> float:
        # Placeholder implementation
        return 3.75
    
@dataclass(frozen=True)
class StudyProgram:
    program_id: str
    name: str
    total_ects: int
    duration_months: int
