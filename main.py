# main.py
# This is the main entry point for the Dashboard application.

import tkinter as tk
import logging

from view import DashboardGUI
from database import Database
from repositories import StudentRepository, ModuleRepository, EnrollmentRepository
from services import DashboardService
from controller import DashboardController

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

# Main function to set up and run the application
def main():
    # Setup database and repositories
    database = Database()
    database.connect()
    database.init_db()

    student_repository = StudentRepository(database=database)
    module_repository = ModuleRepository(database=database)
    enrollment_repository = EnrollmentRepository(database=database)

    service = DashboardService(
        student_repository=student_repository,
        module_repository=module_repository,
        enrollment_repository=enrollment_repository,
    )

    # Setup controller (UML: injects Service only)
    controller = DashboardController(service=service)
    # controller.load_initial_data()  # optional: nur für Demo/Seeding; sonst Module über DB-Skript oder UI pflegen

    # Setup and run GUI
    main_window = tk.Tk()
    dashboard_app = DashboardGUI(master=main_window, controller=controller)
    dashboard_app.pack(fill="both", expand=True)
    dashboard_app.master.title("Dashboard GUI")
    dashboard_app.master.geometry("1100x950")
    main_window.mainloop()

# Entry point
if __name__ == "__main__":
    main()
