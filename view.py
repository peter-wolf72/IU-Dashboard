# view.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from dataclasses import dataclass
from typing import List, Optional

from controller import DashboardController
from model import Student, GoalEvaluation, Module

@dataclass
class TargetMonitoring(ttk.Frame):
    master: tk.Misc
    controller: DashboardController

    def __post_init__(self) -> None:
        super().__init__(self.master)
        self.render()

    def render(self) -> None:
        self.tree = ttk.Treeview(self, columns=("status", "criterion", "value", "target"), show="headings")
        self.tree.heading("status", text="Status")
        self.tree.heading("criterion", text="Kriterium")
        self.tree.heading("value", text="Wert")
        self.tree.heading("target", text="Ziel")
        self.tree.pack(fill="both", expand=True, padx=12, pady=12)

    def update_overview(self, data: List[GoalEvaluation]) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        if not data:
            self.tree.insert("", "end", values=("—", "Kein Student/keine Daten", "", ""))
            return

        for ev in data:
            for c in ev.criteria:
                self.tree.insert(
                    "",
                    "end",
                    values=(str(ev.status), c.name, f"{c.value:.2f}", f"{c.target:.2f}"),
                )

@dataclass
class DataCollection(ttk.Frame):
    master: tk.Misc
    controller: DashboardController

    def __post_init__(self) -> None:
        super().__init__(self.master)
        self._student_rows: dict[str, Student] = {}
        self._modules_by_id: dict[str, Module] = {}
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

        # Wiederhergestellt: Student speichern
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(btns, text="Student speichern", command=self.submit_data).pack(side="left")

        # --- Modul anlegen/aktualisieren (Katalog) ---
        self.catalog_module_id_var = tk.StringVar()
        self.catalog_title_var = tk.StringVar()
        self.catalog_ects_var = tk.StringVar()

        modfrm = ttk.LabelFrame(self, text="Modul anlegen/aktualisieren (Katalog)")
        modfrm.pack(fill="x", padx=12, pady=(0, 12))

        ttk.Label(modfrm, text="Modul-ID").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(modfrm, textvariable=self.catalog_module_id_var, width=16).grid(row=0, column=1, sticky="w", pady=6)

        ttk.Label(modfrm, text="Titel").grid(row=0, column=2, sticky="w", padx=(16, 8), pady=6)
        ttk.Entry(modfrm, textvariable=self.catalog_title_var, width=32).grid(row=0, column=3, sticky="w", pady=6)

        ttk.Label(modfrm, text="ECTS").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(modfrm, textvariable=self.catalog_ects_var, width=10).grid(row=1, column=1, sticky="w", pady=6)

        ttk.Button(modfrm, text="Modul speichern", command=self._save_module).grid(row=1, column=3, sticky="e", padx=8, pady=6)

        # Enrollment Mini-Form
        self.selected_module_id_var = tk.StringVar()
        self.grade_var = tk.StringVar()
        self.passed_var = tk.StringVar()

        enr = ttk.LabelFrame(self, text="Leistung (Enrollment)")
        enr.pack(fill="x", padx=12, pady=(0, 12))

        ttk.Label(enr, text="Modul").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.module_combo = ttk.Combobox(enr, textvariable=self.selected_module_id_var, state="readonly", width=36)
        self.module_combo.grid(row=0, column=1, sticky="w", pady=6)

        ttk.Label(enr, text="Note").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(enr, textvariable=self.grade_var, width=10).grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(enr, text="Bestanden am (TT.MM.JJJJ oder YYYY-MM-DD)").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(enr, textvariable=self.passed_var, width=16).grid(row=2, column=1, sticky="w", pady=6)

        ttk.Button(enr, text="Leistung speichern", command=self._save_enrollment).grid(row=2, column=3, sticky="e", padx=8, pady=6)

        self.refresh_module_dropdown()

        # --- Studentenliste (Persistenz sichtbar + Auswahl lädt Formular) ---
        lst = ttk.LabelFrame(self, text="Angelegte Studenten")
        lst.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.student_tree = ttk.Treeview(lst, columns=("sid", "name", "start"), show="headings", height=8)
        self.student_tree.heading("sid", text="Student-ID")
        self.student_tree.heading("name", text="Name")
        self.student_tree.heading("start", text="Startdatum")
        self.student_tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.student_tree.bind("<<TreeviewSelect>>", self.on_student_selected)

        ttk.Button(lst, text="Liste aktualisieren", command=self.refresh_student_list).pack(anchor="e", padx=8, pady=(0, 8))

        # --- Detailansicht: Enrollments/Module des ausgewählten Students (Master–Detail) ---
        det = ttk.LabelFrame(self, text="Module/Enrollments (ausgewählter Student)")
        det.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.enrollment_tree = ttk.Treeview(
            det,
            columns=("module_id", "title", "ects", "grade", "passed"),
            show="headings",
            height=6,
        )
        self.enrollment_tree.heading("module_id", text="Modul-ID")
        self.enrollment_tree.heading("title", text="Titel")

        # Header rechtsbündig (optional, aber meist gewünscht bei Zahlen/Datum)
        self.enrollment_tree.heading("ects", text="ECTS", anchor="e")
        self.enrollment_tree.heading("grade", text="Note", anchor="e")
        self.enrollment_tree.heading("passed", text="Bestanden am", anchor="e")

        # Zellen rechtsbündig
        self.enrollment_tree.column("ects", anchor="e")
        self.enrollment_tree.column("grade", anchor="e")
        self.enrollment_tree.column("passed", anchor="e")

        self.enrollment_tree.pack(fill="both", expand=True, padx=8, pady=8)

        self._clear_enrollments_view()
        self.refresh_student_list()

    def _clear_enrollments_view(self) -> None:
        for iid in self.enrollment_tree.get_children():
            self.enrollment_tree.delete(iid)
        self.enrollment_tree.insert("", "end", values=("—", "Kein Student ausgewählt", "", "", ""))

    def _render_enrollments(self, student: Student) -> None:
        for iid in self.enrollment_tree.get_children():
            self.enrollment_tree.delete(iid)

        if not getattr(student, "enrollments", None):
            self.enrollment_tree.insert("", "end", values=("—", "Keine Enrollments", "", "", ""))
            return

        for e in student.enrollments:
            mod = e.module
            grade = "" if e.grade is None else f"{e.grade:.2f}"
            passed = "" if e.date_passed is None else e.date_passed.isoformat()
            self.enrollment_tree.insert(
                "",
                "end",
                values=(mod.module_id, mod.title, str(mod.ects), grade, passed),
            )

    def refresh_student_list(self) -> None:
        for iid in self.student_tree.get_children():
            self.student_tree.delete(iid)
        self._student_rows.clear()

        students = self.controller.refresh_student_list()
        for s in students:
            iid = self.student_tree.insert("", "end", values=(s.student_id, s.name, s.start_date.isoformat()))
            self._student_rows[iid] = s

        self._clear_enrollments_view()

    def on_student_selected(self, _evt=None) -> None:
        sel = self.student_tree.selection()
        if not sel:
            self._clear_enrollments_view()
            return
        s = self._student_rows.get(sel[0])
        if s is None:
            self._clear_enrollments_view()
            return

        # Query: vollständiges Aggregate laden (ohne Speichern/Enrichment)
        aggregate = self.controller.get_student_aggregate(s.student_id)

        self.student_id_var.set(aggregate.student_id)
        self.name_var.set(aggregate.name)
        self.start_var.set(aggregate.start_date.isoformat())

        self._render_enrollments(aggregate)

    def submit_data(self) -> None:
        self.controller.process_student_data(self._current_student())
        self.refresh_student_list()

    # NEU: Parser (werden in _save_enrollment genutzt)
    def _parse_grade(self, text: str) -> Optional[float]:
        s = (text or "").strip()
        if not s:
            return None
        s = s.replace(" ", "").replace(",", ".")
        return float(s)

    def _parse_date(self, text: str) -> Optional[datetime.date]:
        s = (text or "").strip()
        if not s:
            return None

        # ISO zuerst (YYYY-MM-DD)
        try:
            return datetime.date.fromisoformat(s)
        except ValueError:
            pass

        # Deutsch: TT.MM.JJJJ / TT.MM.JJ
        for fmt in ("%d.%m.%Y", "%d.%m.%y"):
            try:
                return datetime.datetime.strptime(s, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Ungültiges Datum: {s}")

    def _save_enrollment(self) -> None:
        student = self._current_student()
        if not student.student_id:
            messagebox.showerror("Eingabefehler", "Bitte zuerst eine Student-ID eingeben.")
            return

        display = self.module_combo.get().strip()
        module_id = display.split(" – ", 1)[0].strip() if display else ""
        if not module_id:
            messagebox.showerror("Eingabefehler", "Bitte ein Modul auswählen.")
            return
        if module_id not in self._modules_by_id:
            messagebox.showerror("Eingabefehler", "Ausgewähltes Modul ist nicht (mehr) im Katalog. Bitte neu auswählen.")
            return

        module = Module(module_id=module_id, title="", ects=0)

        try:
            grade = self._parse_grade(self.grade_var.get())
        except ValueError:
            messagebox.showerror("Eingabefehler", "Ungültige Note. Beispiele: 3,3 oder 3.3")
            return

        try:
            passed = self._parse_date(self.passed_var.get())
        except ValueError:
            messagebox.showerror("Eingabefehler", "Ungültiges Datum. Beispiele: 17.02.2026 oder 2026-02-17")
            return

        # Wichtig: Student muss in DB existieren, sonst FK-Fehler in enrollment(student_id,...)
        self.controller.process_student_data(student)

        try:
            self.controller.process_enrollment_data(student, module, grade=grade, date=passed)
        except sqlite3.IntegrityError as e:
            messagebox.showerror("DB-Fehler", f"Speichern fehlgeschlagen (FK). Existiert Student und Modul?\n\n{e}")
            return

        self.refresh_student_list()

    def refresh_module_dropdown(self) -> None:
        modules = self.controller.refresh_module_list()
        self._modules_by_id = {m.module_id: m for m in modules}

        # Anzeige: "ID – Titel (ECTS)"
        values = [f"{m.module_id} – {m.title} ({m.ects} ECTS)" for m in modules]
        self.module_combo["values"] = values

        # Auswahl beibehalten: aus aktuellem Display-String die ID extrahieren
        current_display = self.module_combo.get().strip()
        current_id = current_display.split(" – ", 1)[0].strip() if current_display else ""
        if current_id and current_id in self._modules_by_id:
            m = self._modules_by_id[current_id]
            self.module_combo.set(f"{m.module_id} – {m.title} ({m.ects} ECTS)")
        else:
            self.module_combo.set("")

    def _current_student(self) -> Student:
        sid = self.student_id_var.get().strip()
        name = self.name_var.get().strip()
        start_date = datetime.date.fromisoformat(self.start_var.get().strip())
        return Student(student_id=sid, name=name, start_date=start_date)

    def _save_module(self) -> None:
        module_id = self.catalog_module_id_var.get().strip()
        title = self.catalog_title_var.get().strip()
        ects_txt = self.catalog_ects_var.get().strip()
        ects = int(ects_txt) if ects_txt else 0

        self.controller.process_module_data(Module(module_id=module_id, title=title, ects=ects))
        self.refresh_module_dropdown()

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

        self.target_monitoring = TargetMonitoring(master=self.tab_overview, controller=self.controller)
        self.target_monitoring.pack(fill="both", expand=True)

        # Refresh-Button im Overview-Tab (GUI orchestriert zwischen Subviews)
        top = ttk.Frame(self.tab_overview)
        top.pack(fill="x", padx=12, pady=(12, 0))
        ttk.Button(top, text="Übersicht aktualisieren", command=self._refresh_overview_from_form).pack(side="left")

        self.data_collection = DataCollection(master=self.tab_entry, controller=self.controller)
        self.data_collection.pack(fill="both", expand=True)

    def _refresh_overview_from_form(self) -> None:
        student = self.data_collection._current_student()
        data = self.controller.refresh_dashboard_stats(student)
        self.target_monitoring.update_overview(data)

    def on_window_close(self) -> None:
        try:
            self.controller.shutdown()
        finally:
            self.master.destroy()
