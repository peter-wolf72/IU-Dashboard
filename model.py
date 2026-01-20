# model.py
import datetime
import decimal

class Student:
    def __init__(self, student_id: str, name: str, start_date: datetime.date):
        self.__student_id = student_id
        self.__name = name
        self.__start_date = start_date
    
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
    
    @property
    def student_id(self) -> str:
        return self.__student_id
    @property
    def name(self) -> str:
        return self.__name
    @property
    def start_date(self) -> datetime.date:
        return self.__start_date    
    
class StudyProgram:
    def __init__(self, program_id: int, name: str, total_ects: int, duration_months: int):
        self.__program_id = program_id
        self.__name = name
        self.__total_ects = total_ects
