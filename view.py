# view.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from dataclasses import dataclass
from typing import List, Optional
import logging

from controller import DashboardController
from model import Student, GoalEvaluation, Module


@dataclass
# --- Dashboard Tab with 3 Tiles for Goal Overview ---
class TargetMonitoring(ttk.Frame):
    master: tk.Misc
    controller: DashboardController

    def __post_init__(self) -> None:
        super().__init__(self.master)
        self._student_rows: dict[str, str] = {}  # mapping display-string -> student_id
        self.render()

    def render(self) -> None:
        # --- Header with Student-Dropdown ---
        header = ttk.Frame(self)
        header.pack(fill="x", padx=24, pady=12)

        ttk.Label(header, text="Student:", font=("", 10)).pack(side="left", padx=(0, 8))

        self.student_dropdown = ttk.Combobox(
            header,
            state="readonly",
            width=40,
            font=("", 10),
        )
        self.student_dropdown.pack(side="left", fill="x", expand=True)
        self.student_dropdown.bind("<<ComboboxSelected>>", self.on_student_selected)

        # --- Container for dynamic Tiles ---
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=24, pady=24)

        # Fill dropdown 
        self.refresh_student_dropdown()

    def refresh_student_dropdown(self) -> None:
        students = self.controller.refresh_student_list()
        self._student_rows.clear()

        values = []
        for student in students:
            display = f"{student.student_id} – {student.name}"
            values.append(display)
            self._student_rows[display] = student.student_id

        self.student_dropdown["values"] = values

        current_display = self.student_dropdown.get()
        if current_display and current_display in self._student_rows:
            self.student_dropdown.set(current_display)
        else:
            self.student_dropdown.set("")
            self._show_placeholder()

    def on_student_selected(self, _evt=None) -> None:
        display = self.student_dropdown.get().strip()
        if not display or display not in self._student_rows:
            self._show_placeholder()
            return

        student_id = self._student_rows[display]

        try:
            student = self.controller.get_student_aggregate(student_id)
            data = self.controller.refresh_dashboard_stats(student)
            self.update_overview(data)
        except Exception as e:
            logging.error(f"Error loading student: {e}")
            self._show_placeholder()

    def update_overview(self, data: List[GoalEvaluation]) -> None:
        self._clear_tiles()
        if not data:
            self._show_placeholder()
            return

        from model import Status

        # Sort order for the tiles based on goal title
        sort_order = {
            "Notenschnitt": 0,
            "Bachelorabschluss": 1,
            "Arbeitstempo": 2
        }
        
        # Sort data according to the predefined order, fallback to 999 for unknown titles
        sorted_data = sorted(data, key=lambda evaluation: sort_order.get(evaluation.title, 999))

        # Tile factory: iterates over the provided GoalEvaluations and creates a tile for each, displaying the
        # relevant data and status with appropriate colors and formats. Each tile's content is dynamically generated
        # based on its ui_type, allowing for different visual representations (e.g. big text, dual progress bars, arrows).
        for column, evaluation in enumerate(sorted_data):
            self.container.grid_columnconfigure(column, weight=1, uniform="tile")
            
            tile = ttk.LabelFrame(self.container, text=evaluation.title, padding=16)
            tile.grid(row=0, column=column, sticky="nsew", padx=8, pady=8)

            bg_color = "#c8f7c5" if evaluation.status == Status.GREEN else "#fff4cc" if evaluation.status == Status.YELLOW else "#ffc9c9"

            if evaluation.ui_type == "big_text":
                actual = evaluation.ui_data["actual"]
                target = evaluation.ui_data["target"]

                tk.Label(tile, text=f"Aktuell: {actual:.2f}", font=("", 10)).pack(anchor="center")
                tk.Label(tile, text=f"Ziel: ≤ {target:.2f}", font=("", 10)).pack(anchor="center", pady=(4, 0))

                content = tk.Frame(tile, bg=bg_color)
                content.pack(pady=16, fill="both", expand=True)
                
                # Fontcolor red if Status.RED, otherwise default color; shows the actual value prominently in the tile.
                fg_color = "red" if evaluation.status == Status.RED else "black"
                tk.Label(content, text=f"{actual:.1f}", font=("", 48, "bold"), fg=fg_color, bg=bg_color).pack(expand=True)

            elif evaluation.ui_type == "dual_progress":
                time_percent = evaluation.ui_data["time_percent"]
                cp_percent = evaluation.ui_data["cp_percent"]

                tk.Label(tile, text=f"Zeitfortschritt: {time_percent:.0f}%", font=("", 10)).pack(anchor="center")
                tk.Label(tile, text=f"CP-Fortschritt: {cp_percent:.0f}%", font=("", 10)).pack(anchor="center", pady=(4, 0))

                content = tk.Frame(tile, bg=bg_color)
                content.pack(pady=12, fill="both", expand=True)

                bar_frame = tk.Frame(content, bg=bg_color)
                bar_frame.pack(expand=True)

                tk.Label(bar_frame, text="Zeit", font=("", 9), bg=bg_color).grid(row=0, column=0, padx=4)
                bar_time = ttk.Progressbar(bar_frame, orient="vertical", length=80, mode="determinate")
                bar_time["value"] = min(100, max(0, time_percent))
                bar_time.grid(row=1, column=0, padx=4)

                tk.Label(bar_frame, text="CP", font=("", 9), bg=bg_color).grid(row=0, column=1, padx=4)
                bar_cp = ttk.Progressbar(bar_frame, orient="vertical", length=80, mode="determinate")
                bar_cp["value"] = min(100, max(0, cp_percent))
                bar_cp.grid(row=1, column=1, padx=4)
                
                # Placeholder below the bars to balance the height of the tile and ensure the bars
                # are vertically centered, regardless of the content above.
                tk.Frame(bar_frame, bg=bg_color, height=20, width=1).grid(row=2, column=0, columnspan=2)

            elif evaluation.ui_type == "arrow":
                actual = evaluation.ui_data["actual"]
                target = evaluation.ui_data["target"]
                arrow_char = evaluation.ui_data["arrow"]
                
                fg_col = "green" if evaluation.status == Status.GREEN else "orange" if evaluation.status == Status.YELLOW else "red"

                tk.Label(tile, text=f"Ist: {actual:.2f} CP/Monat", font=("", 10)).pack(anchor="center")
                tk.Label(tile, text=f"Soll: {target:.2f} CP/Monat", font=("", 10)).pack(anchor="center", pady=(4, 0))

                content = tk.Frame(tile, bg=bg_color)
                content.pack(pady=16, fill="both", expand=True)
                tk.Label(content, text=arrow_char, font=("", 48), fg=fg_col, bg=bg_color).pack(expand=True)

    def _clear_tiles(self) -> None:
        """Destroys all dynamically created tiles in the container."""
        for widget in self.container.winfo_children():
            widget.destroy()

    def _show_placeholder(self) -> None:
        """Displays a placeholder message when no student is selected."""
        self._clear_tiles()
        lbl = ttk.Label(
            self.container, 
            text="Für die Visualisierung der Leistung bitte Student auswählen", 
            font=("", 24),
            foreground="gray"
        )
        lbl.place(relx=0.5, rely=0.5, anchor="center")

@dataclass
# --- Data Collection Form for Student and Goal Input ---
class DataCollection(ttk.Frame):
    master: tk.Misc
    controller: DashboardController
    _on_student_saved: Optional[callable] = None  # Callback after student data is saved

    def __post_init__(self) -> None:
        super().__init__(self.master)
        self._student_rows: dict[str, Student] = {} # mapping display-string -> Student
        self._modules_by_id: dict[str, Module] = {} # mapping module_id -> Module
        self._goal_settings: dict[str, float | int] = {} # mapping goal_name -> goal_value
        self.render()

    # Renders the form with fields for student data, goal settings, module management, and enrollment input.
    def render(self) -> None:
        self.student_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.start_var = tk.StringVar(value=datetime.date.today().isoformat())

        # --- Top Tiles (Student | Goal Data) ---
        top_tiles = ttk.Frame(self)
        top_tiles.pack(fill="x", padx=12, pady=12)
        top_tiles.grid_columnconfigure(0, weight=1)
        top_tiles.grid_columnconfigure(1, weight=1)

        student_tile = ttk.LabelFrame(top_tiles, text="Persönliche Daten")
        student_tile.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ttk.Label(student_tile, text="Student-ID").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        ttk.Entry(student_tile, textvariable=self.student_id_var, width=24).grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(8, 4))

        ttk.Label(student_tile, text="Name").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(student_tile, textvariable=self.name_var, width=32).grid(row=1, column=1, sticky="w", padx=(0, 8), pady=4)

        ttk.Label(student_tile, text="Startdatum (YYYY-MM-DD)").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(student_tile, textvariable=self.start_var, width=24).grid(row=2, column=1, sticky="w", padx=(0, 8), pady=4)

        ttk.Button(student_tile, text="Student speichern", command=self.submit_data).grid(
            row=3, column=1, sticky="e", padx=(0, 8), pady=(8, 8)
        )

        goals_tile = ttk.LabelFrame(top_tiles, text="Zieldaten Studium")
        goals_tile.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.goal_duration_var = tk.StringVar(value="")
        self.goal_avg_var = tk.StringVar(value="")
        self.goal_pace_var = tk.StringVar(value="")

        ttk.Label(goals_tile, text="Dauer in Monaten").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        ttk.Entry(goals_tile, textvariable=self.goal_duration_var, width=12).grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(8, 4))

        ttk.Label(goals_tile, text="Notendurchschnitt (Ziel)").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(goals_tile, textvariable=self.goal_avg_var, width=12).grid(row=1, column=1, sticky="w", padx=(0, 8), pady=4)

        ttk.Label(goals_tile, text="Arbeitstempo CP/Monat").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(goals_tile, textvariable=self.goal_pace_var, width=12).grid(row=2, column=1, sticky="w", padx=(0, 8), pady=4)

        ttk.Button(goals_tile, text="Ziele speichern", command=self._save_goal_settings).grid(
            row=3, column=1, sticky="e", padx=(0, 8), pady=(8, 8)
        )

        # --- Add/update module  ---
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

        enrollment = ttk.LabelFrame(self, text="Leistung (Enrollment)")
        enrollment.pack(fill="x", padx=12, pady=(0, 12))

        ttk.Label(enrollment, text="Modul").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.module_combo = ttk.Combobox(enrollment, textvariable=self.selected_module_id_var, state="readonly", width=36)
        self.module_combo.grid(row=0, column=1, sticky="w", pady=6)

        ttk.Label(enrollment, text="Note").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(enrollment, textvariable=self.grade_var, width=10).grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(enrollment, text="Bestanden am (TT.MM.JJJJ oder YYYY-MM-DD)").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(enrollment, textvariable=self.passed_var, width=16).grid(row=2, column=1, sticky="w", pady=6)

        ttk.Button(enrollment, text="Leistung speichern", command=self._save_enrollment).grid(row=2, column=3, sticky="e", padx=8, pady=6)

        self.refresh_module_dropdown()

        # --- List students (Persistence visible + selection loads form) ---
        lst = ttk.LabelFrame(self, text="Angelegte Studenten")
        lst.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.student_tree = ttk.Treeview(lst, columns=("sid", "name", "start"), show="headings", height=8)
        self.student_tree.heading("sid", text="Student-ID")
        self.student_tree.heading("name", text="Name")
        self.student_tree.heading("start", text="Startdatum")
        self.student_tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.student_tree.bind("<<TreeviewSelect>>", self.on_student_selected)

        ttk.Button(lst, text="Liste aktualisieren", command=self.refresh_student_list).pack(anchor="e", padx=8, pady=(0, 8))

        # --- Detail view: Enrollments/Modules of the selected student (Master–Detail) ---
        detail_view = ttk.LabelFrame(self, text="Module/Enrollments (ausgewählter Student)")
        detail_view.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.enrollment_tree = ttk.Treeview(
            detail_view,
            columns=("module_id", "title", "ects", "grade", "passed"),
            show="headings",
            height=6,
        )
        self.enrollment_tree.heading("module_id", text="Modul-ID")
        self.enrollment_tree.heading("title", text="Titel")
        self.enrollment_tree.heading("ects", text="ECTS", anchor="e")
        self.enrollment_tree.heading("grade", text="Note", anchor="e")
        self.enrollment_tree.heading("passed", text="Bestanden am", anchor="e")

        # Columns right-aligned + automatic width
        self.enrollment_tree.column("module_id", anchor="w", width=100, stretch=True)
        self.enrollment_tree.column("title", anchor="w", width=300, stretch=True)
        self.enrollment_tree.column("ects", anchor="e", width=50, stretch=False)
        self.enrollment_tree.column("grade", anchor="e", width=50, stretch=False)
        self.enrollment_tree.column("passed", anchor="e", width=100, stretch=False)

        self.enrollment_tree.pack(fill="both", expand=True, padx=8, pady=8)

        self._clear_enrollments_view()
        
        self.refresh_student_list()

    # Helper to clear the enrollments view
    def _clear_enrollments_view(self) -> None:
        for item_id in self.enrollment_tree.get_children():
            self.enrollment_tree.delete(item_id)
        self.enrollment_tree.insert("", "end", values=("—", "Kein Student ausgewählt", "", "", ""))

    # Helper to render enrollments of the selected student in the detail view
    def _render_enrollments(self, student: Student) -> None:
        for item_id in self.enrollment_tree.get_children():
            self.enrollment_tree.delete(item_id)

        if not getattr(student, "enrollments", None):
            self.enrollment_tree.insert("", "end", values=("—", "Keine Enrollments", "", "", ""))
            return

        for enrollment in student.enrollments:
            module = enrollment.module
            grade = "" if enrollment.grade is None else f"{enrollment.grade:.2f}"
            passed = "" if enrollment.date_passed is None else enrollment.date_passed.isoformat()
            self.enrollment_tree.insert(
                "",
                "end",
                values=(module.module_id, module.title, str(module.ects), grade, passed),
            )

    # Helper to get current student data from form fields
    def refresh_student_list(self) -> None:
        for item_id in self.student_tree.get_children():
            self.student_tree.delete(item_id)
        self._student_rows.clear()

        students = self.controller.refresh_student_list()
        for student in students:
            item_id = self.student_tree.insert(
                "", 
                "end", 
                values=(student.student_id, student.name, student.start_date.isoformat()))
            self._student_rows[item_id] = student

        self._clear_enrollments_view()

    # Event handler: When a student is selected in the treeview, load their aggregate and display enrollments and goals.
    def on_student_selected(self, _evt=None) -> None:
        selection = self.student_tree.selection()
        if not selection:
            self._clear_enrollments_view()
            self._clear_goal_fields()
            return
        student = self._student_rows.get(selection[0])
        if student is None:
            self._clear_enrollments_view()
            self._clear_goal_fields()
            return

        # Query: loads complete aggregate (incl. Enrollments and Goals)
        aggregate = self.controller.get_student_aggregate(student.student_id)

        self.student_id_var.set(aggregate.student_id)
        self.name_var.set(aggregate.name)
        self.start_var.set(aggregate.start_date.isoformat())

        self._render_enrollments(aggregate)
        self._display_goals_from_student(aggregate)

    # Displays the goals of the student in the form fields.
    def _display_goals_from_student(self, student: Student) -> None:
        # default values
        duration = ""
        target_avg = ""
        target_pace = ""

        # Iterate goals
        from model import DeadlineGoal, GradeAverageGoal, CpPaceGoal
        for goal in student.goals:
            if isinstance(goal, DeadlineGoal):
                duration = str(goal.duration_months)
            elif isinstance(goal, GradeAverageGoal):
                target_avg = str(goal.target_avg).replace(".", ",")
            elif isinstance(goal, CpPaceGoal):
                target_pace = str(goal.target_cp_per_month).replace(".", ",")

        self.goal_duration_var.set(duration)
        self.goal_avg_var.set(target_avg)
        self.goal_pace_var.set(target_pace)

    # helper to clear goal fields when no student is selected or on error
    def _clear_goal_fields(self) -> None:
        self.goal_duration_var.set("")
        self.goal_avg_var.set("")
        self.goal_pace_var.set("")

    # save student data; called by "Student speichern" button
    def submit_data(self) -> None:
        self.controller.process_student_data(self._current_student())
        self.refresh_student_list()
        messagebox.showinfo("Student gespeichert", "Studentendaten wurden erfolgreich übernommen.")
        
        # Callback: synchronize dashboard view after saving student data (e.g. to update dropdowns or trigger selection)
        if self._on_student_saved:
            self._on_student_saved()

    # helper to parse grade input (e.g. "3,3" or "3.3") into float; returns None if empty
    def _parse_grade(self, text: str) -> Optional[float]:
        s = (text or "").strip()
        if not s:
            return None
        s = s.replace(" ", "").replace(",", ".")
        return float(s)

    # helper to parse date input in various formats (e.g. "17.02.2026" or "2026-02-17") into datetime.date; returns None if empty
    def _parse_date(self, text: str) -> Optional[datetime.date]:
        s = (text or "").strip()
        if not s:
            return None

        # ISO first (YYYY-MM-DD)
        try:
            return datetime.date.fromisoformat(s)
        except ValueError:
            pass

        # German: DD.MM.YYYY / DD.MM.YY
        for fmt in ("%d.%m.%Y", "%d.%m.%y"):
            try:
                return datetime.datetime.strptime(s, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Ungültiges Datum: {s}")

    # Save enrollment data; called by "Leistung speichern" button
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

        self.controller.process_student_data(student)

        try:
            self.controller.process_enrollment_data(student, module, grade=grade, date=passed)
        except sqlite3.IntegrityError as e:
            messagebox.showerror("DB-Fehler", f"Speichern fehlgeschlagen (FK). Existiert Student und Modul?\n\n{e}")
            return

        self.refresh_student_list()

    # Refresh module list for dropdown; called after saving a module or when opening the tab
    def refresh_module_dropdown(self) -> None:
        modules = self.controller.refresh_module_list()
        self._modules_by_id = {m.module_id: m for m in modules}

        # Display strings: "Modul-ID – Titel (ECTS ECTS)"
        values = [f"{m.module_id} – {m.title} ({m.ects} ECTS)" for m in modules]
        self.module_combo["values"] = values

        # Keep selection: extract ID from current display string
        current_display = self.module_combo.get().strip()
        current_id = current_display.split(" – ", 1)[0].strip() if current_display else ""
        if current_id and current_id in self._modules_by_id:
            m = self._modules_by_id[current_id]
            self.module_combo.set(f"{m.module_id} – {m.title} ({m.ects} ECTS)")
        else:
            self.module_combo.set("")

    # Helper to construct a Student object from the form fields; used when saving student data or enrollments
    def _current_student(self) -> Student:
        student_id = self.student_id_var.get().strip()
        name = self.name_var.get().strip()
        start_date = datetime.date.fromisoformat(self.start_var.get().strip())
        return Student(student_id=student_id, name=name, start_date=start_date)

    # Save module data; called by "Modul speichern" button
    def _save_module(self) -> None:
        module_id = self.catalog_module_id_var.get().strip()
        title = self.catalog_title_var.get().strip()
        ects_txt = self.catalog_ects_var.get().strip()
        ects = int(ects_txt) if ects_txt else 0

        self.controller.process_module_data(Module(module_id=module_id, title=title, ects=ects))
        self.refresh_module_dropdown()
        messagebox.showinfo("Module gespeichert", "Moduldaten wurden erfolgreich übernommen.")

    # Save goal settings; called by "Ziele speichern" button
    def _save_goal_settings(self) -> None:
        # Parse and validate goal inputs; show error message if invalid
        try:
            duration = int((self.goal_duration_var.get() or "").strip())
            target_avg = float((self.goal_avg_var.get() or "").strip().replace(",", "."))
            target_pace = float((self.goal_pace_var.get() or "").strip().replace(",", "."))
        except ValueError:
            messagebox.showerror(
                "Eingabefehler",
                "Bitte gültige Zahlen eingeben.\n"
                "Beispiele: Dauer=36, Notenziel=2,5, CP/Monat=5,0",
            )
            return

        # Get the current student ID
        student_id = self.student_id_var.get().strip()
        if not student_id:
            messagebox.showerror("Eingabefehler", "Bitte zuerst eine Student-ID eingeben.")
            return

        try:
            self.controller.process_goal_data(student_id, duration, target_avg, target_pace)
            messagebox.showinfo("Ziele gespeichert", "Zieldaten wurden erfolgreich gespeichert.")
        except ValueError as e:
            messagebox.showerror("Eingabefehler", str(e))
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")

@dataclass
# --- Main Dashboard View with Tabs for Overview and Data Collection ---
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

        # Refresh button in the Overview tab (GUI orchestrates between subviews)
        top = ttk.Frame(self.tab_overview)
        top.pack(fill="x", padx=12, pady=(12, 0))
        ttk.Button(top, text="Übersicht aktualisieren", command=self._refresh_overview_from_form).pack(side="left")

        self.data_collection = DataCollection(master=self.tab_entry, controller=self.controller)
        self.data_collection.pack(fill="both", expand=True)
        
        # Callback wiring: After saving a student -> update dropdown in overview tab
        self.data_collection._on_student_saved = self.sync_student_dropdown


    # orchestrates synchronization between tabs: After saving a student in the "Data Collection" tab, 
    # the dropdown in the "Target Monitoring" tab is updated.
    def sync_student_dropdown(self) -> None:
        self.target_monitoring.refresh_student_dropdown()
        logging.info("Student dropdown in Target Monitoring refreshed after saving student data in Data Collection tab.")

    # Helper to refresh the overview tab based on the currently selected student in the data collection form.
    def _refresh_overview_from_form(self) -> None:
        student = self.data_collection._current_student()
        data = self.controller.refresh_dashboard_stats(student)
        self.target_monitoring.update_overview(data)

    def on_window_close(self) -> None:
        try:
            self.controller.shutdown()
        finally:
            self.master.destroy()
