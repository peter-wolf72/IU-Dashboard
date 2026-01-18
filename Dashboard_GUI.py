import tkinter as tk
from tkinter import ttk
import datetime
import decimal
import sqlite3
import logging


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

class DashboardGUI(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.title("Dashboard GUI")

        #Geometry-Management
        self.master.geometry("800x600")
        self.pack(fill="both", expand=True)

        # Handle window close event
        self.master.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Initialize database connection
        try:
            self.conn = sqlite3.connect('dashboard.db')
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}.")
            self.conn = None
        else:
            self.cursor = self.conn.cursor()
            logging.info("Database connected successfully.")
        
        self.create_widgets()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_overview = ttk.Frame(self.notebook)
        self.tab_entry = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_overview, text="Zielübersicht")
        self.notebook.add(self.tab_entry, text="Datenerfassung")

        # Platzhalter-Inhalte (kannst du später ersetzen)
        ttk.Label(self.tab_overview, text="(Platzhalter) Zielübersicht").pack(
            padx=12, pady=12, anchor="w"
        )
        ttk.Label(self.tab_entry, text="(Platzhalter) Datenerfassung").pack(
            padx=12, pady=12, anchor="w"
        )

            
    def close(self):
        self.conn.close()

    def on_window_close(self):
        # Ensure resources are cleaned up properly
        try:
            self.close()
            logging.info("Resources cleaned up successfully.")
        finally:
            self.master.destroy()

if __name__ == "__main__":
    main_window = tk.Tk()
    dashboard_app = DashboardGUI(main_window)
    main_window.mainloop()