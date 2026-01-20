# main.py
import tkinter as tk
from gui import DashboardGUI
import logging
from database import Database

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')


def main():
    db = Database()
    db.connect()
    db.init_db()

    main_window = tk.Tk()
    dashboard_app = DashboardGUI(main_window, db)
    dashboard_app.pack(fill="both", expand=True)
    dashboard_app.master.title("Dashboard GUI")
    dashboard_app.master.geometry("800x600")
    main_window.mainloop()    

if __name__ == "__main__":
    main()
