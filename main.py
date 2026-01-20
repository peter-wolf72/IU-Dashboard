# main.py
import tkinter as tk
from view import DashboardGUI
import logging
from database import Database
from repositories import StudentRepository
from services import DashboardService
from controller import DashboardController


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')


def main():
    db = Database()
    db.connect()
    db.init_db()

    student_repo = StudentRepository(db)
    service = DashboardService(student_repo)
    controller = DashboardController(service, db)


    main_window = tk.Tk()
    dashboard_app = DashboardGUI(master=main_window, controller=controller)
    dashboard_app.pack(fill="both", expand=True)
    dashboard_app.master.title("Dashboard GUI")
    dashboard_app.master.geometry("800x600")
    main_window.mainloop()    

if __name__ == "__main__":
    main()
