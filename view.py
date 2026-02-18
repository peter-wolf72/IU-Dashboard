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
class TargetMonitoring(ttk.Frame):
    master: tk.Misc
    controller: DashboardController

    def __post_init__(self) -> None:
        super().__init__(self.master)
        self._tiles: dict[str, ttk.LabelFrame] = {}
        self._tile_labels: dict[str, dict[str, tk.Label]] = {}
        self._tile_bars: dict[str, ttk.Progressbar] = {}
        self._student_rows: dict[str, str] = {}  # mapping display-string -> student_id
        self.render()

    def render(self) -> None:
        # --- Header mit Student-Dropdown ---
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

        # --- Container für 3 Kacheln in einer Zeile ---
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=24, pady=24)
        container.grid_columnconfigure(0, weight=1, uniform="tile")
        container.grid_columnconfigure(1, weight=1, uniform="tile")
        container.grid_columnconfigure(2, weight=1, uniform="tile")

        # Kachel 1: Notendurchschnitt
        tile_grade = ttk.LabelFrame(container, text="Notendurchschnitt", padding=16)
        tile_grade.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self._tiles["grade"] = tile_grade

        # Captions OHNE Farbe, zentriert oben
        lbl_grade_actual_caption = tk.Label(tile_grade, text="Aktuell:", font=("", 10))
        lbl_grade_actual_caption.pack(anchor="center")
        lbl_grade_actual = tk.Label(tile_grade, text="—", font=("", 10))
        lbl_grade_actual.pack(anchor="center")

        lbl_grade_target_caption = tk.Label(tile_grade, text="Ziel:", font=("", 10))
        lbl_grade_target_caption.pack(anchor="center", pady=(8, 0))
        lbl_grade_target = tk.Label(tile_grade, text="—", font=("", 10))
        lbl_grade_target.pack(anchor="center")

        # Inner Frame für farbigen Content
        grade_content = tk.Frame(tile_grade, bg="white")
        grade_content.pack(pady=16, fill="both", expand=True)

        lbl_grade_big = tk.Label(grade_content, text="—", font=("", 48, "bold"), fg="red", bg="white")
        lbl_grade_big.pack(pady=16, anchor="center")

        self._tile_labels["grade"] = {
            "actual": lbl_grade_actual,
            "target": lbl_grade_target,
            "big": lbl_grade_big,
            "content_frame": grade_content,
        }

        # Kachel 2: Bachelorabschluss / Deadline
        tile_deadline = ttk.LabelFrame(container, text="Bachelorabschluss", padding=16)
        tile_deadline.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self._tiles["deadline"] = tile_deadline

        lbl_deadline_time = tk.Label(tile_deadline, text="Zeitfortschritt: —", font=("", 10), anchor="center")
        lbl_deadline_time.pack(anchor="center")
        lbl_deadline_cp = tk.Label(tile_deadline, text="CP-Fortschritt: —", font=("", 10), anchor="center")
        lbl_deadline_cp.pack(anchor="center", pady=(4, 0))

        # Inner Frame für Balken (farbig)
        deadline_content = tk.Frame(tile_deadline, bg="white")
        deadline_content.pack(pady=12, fill="both", expand=True)

        bar_frame = tk.Frame(deadline_content)
        bar_frame.pack(expand=True)  # expand=True für vertikale Zentrierung

        lbl_bar_left = tk.Label(bar_frame, text="Zeit", font=("", 9), bg="white")
        lbl_bar_left.grid(row=0, column=0, padx=4)
        bar_time = ttk.Progressbar(bar_frame, orient="vertical", length=80, mode="determinate")
        bar_time.grid(row=1, column=0, padx=4)

        lbl_bar_right = tk.Label(bar_frame, text="CP", font=("", 9), bg="white")
        lbl_bar_right.grid(row=0, column=1, padx=4)
        bar_cp = ttk.Progressbar(bar_frame, orient="vertical", length=80, mode="determinate")
        bar_cp.grid(row=1, column=1, padx=4)

        self._tile_labels["deadline"] = {
            "time": lbl_deadline_time,
            "cp": lbl_deadline_cp,
            "content_frame": deadline_content,
        }
        self._tile_bars["deadline_time"] = bar_time
        self._tile_bars["deadline_cp"] = bar_cp

        # Kachel 3: Arbeitstempo
        tile_pace = ttk.LabelFrame(container, text="Arbeitstempo", padding=16)
        tile_pace.grid(row=0, column=2, sticky="nsew", padx=8, pady=8)
        self._tiles["pace"] = tile_pace

        lbl_pace_actual = tk.Label(tile_pace, text="Ist: — CP/Monat", font=("", 10), anchor="center")
        lbl_pace_actual.pack(anchor="center")
        lbl_pace_target = tk.Label(tile_pace, text="Soll: — CP/Monat", font=("", 10), anchor="center")
        lbl_pace_target.pack(anchor="center", pady=(4, 0))

        # Inner Frame für Pfeil (farbig)
        pace_content = tk.Frame(tile_pace, bg="white")
        pace_content.pack(pady=16, fill="both", expand=True)

        lbl_pace_arrow = tk.Label(pace_content, text="—", font=("", 48), fg="black", bg="white")
        lbl_pace_arrow.pack(expand=True)  # expand=True für vertikale UND horizontale Zentrierung

        self._tile_labels["pace"] = {
            "actual": lbl_pace_actual,
            "target": lbl_pace_target,
            "arrow": lbl_pace_arrow,
            "content_frame": pace_content,
        }

        # JETZT: Dropdown füllen (nach Kacheln initialisiert)
        self.refresh_student_dropdown()

    def refresh_student_dropdown(self) -> None:
        """
        Lädt aktuelle Studentenliste und befüllt das Dropdown.
        Wird aufgerufen nach Student anlegen oder beim Öffnen des Tabs.
        """
        students = self.controller.refresh_student_list()
        self._student_rows.clear()

        # Anzeige-Strings: "Student-ID – Name"
        values = []
        for s in students:
            display = f"{s.student_id} – {s.name}"
            values.append(display)
            self._student_rows[display] = s.student_id

        self.student_dropdown["values"] = values

        # Aktuell selektierte ID beibehalten (falls vorhanden)
        current_display = self.student_dropdown.get()
        if current_display and current_display in self._student_rows:
            self.student_dropdown.set(current_display)
        else:
            self.student_dropdown.set("")
            self._clear_tiles()

    def on_student_selected(self, _evt=None) -> None:
        """
        Event-Handler: Wenn Student im Dropdown ausgewählt wird,
        lade sein Aggregat und zeige die Ziele an.
        """
        display = self.student_dropdown.get().strip()
        if not display or display not in self._student_rows:
            self._clear_tiles()
            return

        student_id = self._student_rows[display]

        try:
            # Query: Aggregat laden (inkl. Goals)
            student = self.controller.get_student_aggregate(student_id)
            # Evaluiere Goals
            data = self.controller.refresh_dashboard_stats(student)
            # Update Kacheln
            self.update_overview(data)
        except Exception as e:
            logging.error(f"Fehler beim Laden des Students: {e}")
            self._clear_tiles()

    def update_overview(self, data: List[GoalEvaluation]) -> None:
        """
        Aktualisiert die 3 Tiles basierend auf den GoalEvaluation-Objekten.
        RDM-konform: View kennt nur Darstellung (Farbe, Werte); Logik liegt in Goal.evaluate().
        """
        if not data:
            self._clear_tiles()
            return

        # Mapping: Erkenne Goal anhand criteria-Namen (alternativ: Goal-Titel-Matching)
        from model import Status

        for ev in data:
            if not ev.criteria:
                continue

            first_crit = ev.criteria[0]
            name_lower = first_crit.name.lower()

            # 1) Notendurchschnitt
            if "notenschnitt" in name_lower:
                actual = first_crit.value
                target = first_crit.target
                self._tile_labels["grade"]["actual"].config(text=f"{actual:.2f}")
                self._tile_labels["grade"]["target"].config(text=f"≤ {target:.2f}")
                self._tile_labels["grade"]["big"].config(text=f"{actual:.1f}")
                self._set_tile_color("grade", ev.status)

            # 2) Deadline / Plan
            elif "deadline" in name_lower or "cp%" in name_lower:
                # ev hat 2 criteria: CP%, Delta
                cp_val = ev.criteria[0].value
                cp_target = ev.criteria[0].target
                delta_val = ev.criteria[1].value if len(ev.criteria) > 1 else 0.0

                self._tile_labels["deadline"]["time"].config(text=f"Zeitfortschritt: {cp_target:.0f}%")
                self._tile_labels["deadline"]["cp"].config(text=f"CP-Fortschritt: {cp_val:.0f}%")

                self._tile_bars["deadline_time"]["value"] = min(100, max(0, cp_target))
                self._tile_bars["deadline_cp"]["value"] = min(100, max(0, cp_val))

                self._set_tile_color("deadline", ev.status)

            # 3) Arbeitstempo (CP Pace)
            elif "pace" in name_lower or "cp/monat" in name_lower:
                pace_actual = first_crit.value
                pace_target = first_crit.target

                self._tile_labels["pace"]["actual"].config(text=f"Ist: {pace_actual:.2f} CP/Monat")
                self._tile_labels["pace"]["target"].config(text=f"Soll: {pace_target:.2f} CP/Monat")

                # Pfeil: ↓ wenn zu langsam, ↑ wenn gut/schnell
                if ev.status == Status.GREEN:
                    arrow = "↑"
                    arrow_color = "green"
                elif ev.status == Status.YELLOW:
                    arrow = "→"
                    arrow_color = "orange"
                else:
                    arrow = "↓"
                    arrow_color = "red"

                self._tile_labels["pace"]["arrow"].config(text=arrow, fg=arrow_color)
                self._set_tile_color("pace", ev.status)

    def _set_tile_color(self, tile_key: str, status) -> None:
        """
        Färbt nur den Content-Frame (nicht die ganze Kachel).
        """
        from model import Status
        
        if status == Status.GREEN:
            bg_color = "#c8f7c5"
        elif status == Status.YELLOW:
            bg_color = "#fff4cc"
        else:
            bg_color = "#ffc9c9"

        # Nur Content-Frame färben
        content_frame = self._tile_labels[tile_key].get("content_frame")
        if content_frame:
            content_frame.configure(bg=bg_color)
            for child in content_frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=bg_color)
                elif isinstance(child, tk.Frame):
                    child.configure(bg=bg_color)
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label):
                            grandchild.configure(bg=bg_color)

    def _clear_tiles(self) -> None:
        """
        Guard: nur wenn Labels bereits existieren.
        """
        if not self._tile_labels.get("grade"):
            return

        self._tile_labels["grade"]["actual"].config(text="—")
        self._tile_labels["grade"]["target"].config(text="—")
        self._tile_labels["grade"]["big"].config(text="—", fg="gray", bg="white")

        self._tile_labels["deadline"]["time"].config(text="Zeitfortschritt: —")
        self._tile_labels["deadline"]["cp"].config(text="CP-Fortschritt: —")
        self._tile_bars["deadline_time"]["value"] = 0
        self._tile_bars["deadline_cp"]["value"] = 0

        self._tile_labels["pace"]["actual"].config(text="Ist: — CP/Monat")
        self._tile_labels["pace"]["target"].config(text="Soll: — CP/Monat")
        self._tile_labels["pace"]["arrow"].config(text="—", fg="gray", bg="white")

        # Content-Frames auf weiß zurücksetzen
        for tile_key in ["grade", "deadline", "pace"]:
            content_frame = self._tile_labels[tile_key].get("content_frame")
            if content_frame:
                content_frame.configure(bg="white")
                for child in content_frame.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg="white")
                    elif isinstance(child, tk.Frame):
                        child.configure(bg="white")

@dataclass
class DataCollection(ttk.Frame):
    master: tk.Misc
    controller: DashboardController
    _on_student_saved: Optional[callable] = None  # Callback nach Speichern

    def __post_init__(self) -> None:
        super().__init__(self.master)
        self._student_rows: dict[str, Student] = {}
        self._modules_by_id: dict[str, Module] = {}
        self._goal_settings: dict[str, float | int] = {}
        self.render()

    def render(self) -> None:
        self.student_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.start_var = tk.StringVar(value=datetime.date.today().isoformat())

        # --- NEU: Zwei Kacheln nebeneinander (Student | Zieldaten) ---
        top_tiles = ttk.Frame(self)
        top_tiles.pack(fill="x", padx=12, pady=12)
        top_tiles.grid_columnconfigure(0, weight=1)
        top_tiles.grid_columnconfigure(1, weight=1)

        student_tile = ttk.LabelFrame(top_tiles, text="Persönlichen Daten")
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
        self.enrollment_tree.heading("ects", text="ECTS", anchor="e")
        self.enrollment_tree.heading("grade", text="Note", anchor="e")
        self.enrollment_tree.heading("passed", text="Bestanden am", anchor="e")

        # Spalten rechtsbündig + automatische Breite
        self.enrollment_tree.column("module_id", anchor="w", width=100, stretch=True)
        self.enrollment_tree.column("title", anchor="w", width=300, stretch=True)
        self.enrollment_tree.column("ects", anchor="e", width=50, stretch=False)
        self.enrollment_tree.column("grade", anchor="e", width=50, stretch=False)
        self.enrollment_tree.column("passed", anchor="e", width=100, stretch=False)

        self.enrollment_tree.pack(fill="both", expand=True, padx=8, pady=8)

        self._clear_enrollments_view()
        self.refresh_student_list()  # ← WIEDER EINBAUEN: notwendig für initiales Füllen des Treeviews

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
            self._clear_goal_fields()
            return
        s = self._student_rows.get(sel[0])
        if s is None:
            self._clear_enrollments_view()
            self._clear_goal_fields()
            return

        # Query: vollständiges Aggregate laden (inkl. Enrollments UND Goals)
        aggregate = self.controller.get_student_aggregate(s.student_id)

        self.student_id_var.set(aggregate.student_id)
        self.name_var.set(aggregate.name)
        self.start_var.set(aggregate.start_date.isoformat())

        self._render_enrollments(aggregate)
        self._display_goals_from_student(aggregate)

    def _display_goals_from_student(self, student: Student) -> None:
        """
        Extrahiert Zielwerte aus student.goals und befüllt die Ziel-Felder.
        """
        # Default-Werte (falls keine Goals gesetzt)
        duration = ""
        target_avg = ""
        target_pace = ""

        # Goals durchsuchen
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

    def _clear_goal_fields(self) -> None:
        """
        Leert die Ziel-Felder (z.B. bei keiner Student-Auswahl).
        """
        self.goal_duration_var.set("")
        self.goal_avg_var.set("")
        self.goal_pace_var.set("")

    def submit_data(self) -> None:
        self.controller.process_student_data(self._current_student())
        self.refresh_student_list()
        messagebox.showinfo("Student gespeichert", "Studentendaten wurden erfolgreich übernommen.")
        
        # Callback: Synchronisiere Dropdown im anderen Tab
        if self._on_student_saved:
            self._on_student_saved()

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
        messagebox.showinfo("Module gespeichert", "Moduldaten wurden erfolgreich übernommen.")

    def _save_goal_settings(self) -> None:
        """
        Validiert Eingabewerte und delegiert an Controller.
        """
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

        # Hole die aktuelle Student-ID
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
        
        # Callback-Verkabelung: Nach Student speichern -> Dropdown aktualisieren
        self.data_collection._on_student_saved = self.sync_student_dropdown

    def sync_student_dropdown(self) -> None:
        """
        Orchestriert die Sync zwischen Tabs:
        Nach Speichern eines Students im Tab "Datenerfassung"
        wird das Dropdown im Tab "Zielüberwachung" aktualisiert.
        """
        self.target_monitoring.refresh_student_dropdown()

    def _refresh_overview_from_form(self) -> None:
        student = self.data_collection._current_student()
        data = self.controller.refresh_dashboard_stats(student)
        self.target_monitoring.update_overview(data)

    def on_window_close(self) -> None:
        try:
            self.controller.shutdown()
        finally:
            self.master.destroy()
