#
import tkinter as tk
from tkinter import ttk
from database import Database


class DashboardGUI(tk.Frame):
    def __init__(self, master: tk.Tk, db: Database):
        super().__init__(master)
        self.master = master
        self.db = db

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

    def on_window_close(self):
        # Ensure resources are cleaned up properly
        try:
            self.db.close()
        finally:
            self.master.destroy()

