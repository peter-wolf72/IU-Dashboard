#
import tkinter as tk
from tkinter import ttk
from controller import DashboardController
import datetime

class DashboardGUI(tk.Frame):
    def __init__(self, master: tk.Tk, controller: DashboardController):
        super().__init__(master)
        self.master = master
        self.controller = controller

        # Handle window close event
        self.master.protocol("WM_DELETE_WINDOW", self.on_window_close)
                
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

    def on_save_student(self):
        sid = self.student_id_var.get().strip()
        name = self.name_var.get().strip()
        start_date = datetime.date.fromisoformat(self.start_var.get().strip())
        self.controller.save_student(sid, name, start_date)

    def on_load_overview(self):
        sid = self.student_id_var.get().strip()
        data = self.controller.get_overview(sid)
        if "error" in data:
            self.overview_label.config(text=data["error"])
        else:
            self.overview_label.config(
                text=f"Name: {data['student_name']}\nNotenschnitt: {data['average_grade']}\nCP/Monat: {data['cp_per_month']}"
            )

    def on_window_close(self):
        try:
            self.controller.shutdown()
        finally:
            self.master.destroy()
