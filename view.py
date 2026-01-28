# view.py
import tkinter as tk
from tkinter import ttk
import datetime
from dataclasses import dataclass
from typing import List, Optional

from controller import DashboardController
from model import Student, GoalEvaluation

@dataclass
class TargetMonitoring(ttk.Frame):
    master: tk.Misc

    def __post_init__(self) -> None:
        super().__init__(self.master)
        self.render()

    def render(self) -> None:
        self.tree = ttk.Treeview(self, columns=("status", "value", "target", "value2"), show="headings")
        self.tree.heading("status", text="Status")
        self.tree.heading("value", text="Wert")
        self.tree.heading("target", text="Ziel")
        self.tree.heading("value2", text="Delta")
        self.tree.pack(fill="both", expand=True, padx=12, pady=12)

    def update_overview(self, data: List[GoalEvaluation]) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        if not data:
            self.tree.insert("", "end", values=("—", "Kein Student/keine Daten", "", ""))
            return

        for ev in data:
            self.tree.insert(
                "",
                "end",
                values=(f"{ev.title}: {ev.status}", f"{ev.value:.2f}", f"{ev.target:.2f}", f"{ev.value2:.2f}"),
            )


@dataclass
class DataCollection(ttk.Frame):
    master: tk.Misc
    controller: DashboardController
    on_overview_loaded: callable  # callback(List[GoalEvaluation])

    def __post_init__(self) -> None:
        super().__init__(self.master)
        self.render()

    def render(self) -> None:
        self.student_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.start_var = tk.StringVar(value=datetime.date.today().isoformat())

        frm = ttk.Frame(self)
        frm.pack(fill="x", padx=12, pady=12)

        ttk.Label(frm, text="Student-ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.student_id_var, width=24).grid(row=0, column=1, sticky="w", padx=(8, 0))

        ttk.Label(frm, text="Name").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.name_var, width=32).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(frm, text="Startdatum (YYYY-MM-DD)").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.start_var, width=24).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=12, pady=(0, 12))

        ttk.Button(btns, text="Student speichern", command=self._save_student).pack(side="left")
        ttk.Button(btns, text="Übersicht laden", command=self._load_overview).pack(side="left", padx=(8, 0))

        # Enrollment Mini-Form
        self.module_id_var = tk.StringVar()
        self.grade_var = tk.StringVar()
        self.passed_var = tk.StringVar()

        enr = ttk.LabelFrame(self, text="Leistung (Enrollment)")
        enr.pack(fill="x", padx=12, pady=(0, 12))

        ttk.Label(enr, text="Modul-ID").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(enr, textvariable=self.module_id_var, width=16).grid(row=0, column=1, sticky="w", pady=6)

        ttk.Label(enr, text="Note").grid(row=0, column=2, sticky="w", padx=(16, 8), pady=6)
        ttk.Entry(enr, textvariable=self.grade_var, width=10).grid(row=0, column=3, sticky="w", pady=6)

        ttk.Label(enr, text="Bestanden am (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(enr, textvariable=self.passed_var, width=16).grid(row=1, column=1, sticky="w", pady=6)

        ttk.Button(enr, text="Leistung speichern", command=self._save_enrollment).grid(row=1, column=3, sticky="e", padx=8, pady=6)

    def _save_student(self) -> None:
        sid = self.student_id_var.get().strip()
        name = self.name_var.get().strip()
        start_date = datetime.date.fromisoformat(self.start_var.get().strip())
        self.controller.save_student(Student(student_id=sid, name=name, start_date=start_date, program_id=self.controller.program.program_id))

    def _save_enrollment(self) -> None:
        sid = self.student_id_var.get().strip()
        mid = self.module_id_var.get().strip()

        grade_txt = self.grade_var.get().strip()
        grade: Optional[float] = float(grade_txt) if grade_txt else None

        passed_txt = self.passed_var.get().strip()
        passed: Optional[datetime.date] = datetime.date.fromisoformat(passed_txt) if passed_txt else None

        self.controller.add_or_update_enrollment(sid, mid, grade, passed)

    def _load_overview(self) -> None:
        sid = self.student_id_var.get().strip()
        data = self.controller.compute_overview(sid)
        self.on_overview_loaded(data)


@dataclass
class DashboardGUI(tk.Frame):
    master: tk.Tk
    controller: DashboardController

    def __post_init__(self) -> None:
        super().__init__(self.master)

        self.master.protocol("WM_DELETE_WINDOW", self.on_window_close)

        self.create_widgets()

    def create_widgets(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_overview = ttk.Frame(self.notebook)
        self.tab_entry = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_overview, text="Zielüberwachung")
        self.notebook.add(self.tab_entry, text="Datenerfassung")

        self.target_monitoring = TargetMonitoring(master=self.tab_overview)
        self.target_monitoring.pack(fill="both", expand=True)

        self.data_collection = DataCollection(
            master=self.tab_entry,
            controller=self.controller,
            on_overview_loaded=self.target_monitoring.update_overview,
        )
        self.data_collection.pack(fill="both", expand=True)

    def on_window_close(self) -> None:
        try:
            self.controller.shutdown()
        finally:
            self.master.destroy()
