# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit,
    QListWidget, QMessageBox, QTabWidget, QHBoxLayout, QApplication, QComboBox,
    QFileDialog, QProgressBar, QCalendarWidget, QSplitter, QDialog, QPlainTextEdit,
    QGraphicsDropShadowEffect, QMenu
)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QColor, QTextCharFormat
from datetime import datetime, date, timedelta
from db import database as db
import re, json, os

from core.config import load_cfg, save_cfg, user_bucket
from core.theme import (
    apply_theme_to_app,
    apply_accent_to_window,
    apply_aurora_effects_if_needed,
)


# -------------------- Config (global + per-user) --------------------
CONFIG_FILE = "app_settings.json"

# -------------------- Small helpers --------------------
def _today_iso() -> str:
    return date.today().isoformat()

# -------------------- Main Window --------------------
class MainWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user  # (id, username, xp)
        self.setWindowTitle("Task5")
        self.resize(1000, 700)

        # settings
        self.cfg = load_cfg()                  # global (theme/accent)
        self.ucfg = user_bucket(self.cfg, self.user[0])  # per-user bucket

        # --- one-time migration from old global keys (if present) ---
        _legacy = ("groups","task_groups","priorities","completion_log","reminded")
        migrated = False
        for k in _legacy:
            if k in self.cfg and k not in self.ucfg:
                self.ucfg[k] = self.cfg.pop(k)
                migrated = True
        if migrated:
            save_cfg(self.cfg)
        # ------------------------------------------------------------

        # layout
        self.tabs = QTabWidget(self)
        root = QVBoxLayout(self)
        root.addWidget(self.tabs)
        self.init_task_tab()
        self.init_calendar_tab()
        self.init_settings_tab()

        apply_theme_to_app(self.cfg.get("theme", "aurora"))
        apply_accent_to_window(self, self.cfg.get("accent", "#7AA2F7"))
        apply_aurora_effects_if_needed(self, self.cfg)


        # initial data
        self.refresh_group_controls()
        self.refresh_tasks()

        # reminders
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_due_reminders)
        self.reminder_timer.start(60_000)
        self.check_due_reminders()

    # -------------------- Task tab --------------------
    def init_task_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header: Progress + Streak
        hdr = QHBoxLayout()
        left = QHBoxLayout()
        left.addWidget(QLabel("User Progress:"))
        self.user_label = QLabel("XP: 0")
        self.level_label = QLabel("Level: 0")
        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        self.level_bar.setValue(0)
        self.level_bar.setFixedWidth(220)
        self.level_bar.setTextVisible(True)
        self.level_bar.setFormat("%p%")

        left.addSpacing(12)
        left.addWidget(self.user_label)
        left.addSpacing(8)
        left.addWidget(self.level_label)
        left.addSpacing(8)
        left.addWidget(self.level_bar)

        right = QHBoxLayout()
        self.streak_label = QLabel("🔥 Streak: 0")
        right.addWidget(self.streak_label)

        hdr.addLayout(left)
        hdr.addStretch(1)
        hdr.addLayout(right)
        layout.addLayout(hdr)

        # Row: Title + Group + Priority
        trow = QHBoxLayout()
        trow.addWidget(QLabel("Task Title:"))
        self.task_input = QLineEdit(placeholderText="Enter task title")
        self.task_input.setToolTip("Required. Max 100 characters.")
        trow.addWidget(self.task_input, 1)

        trow.addSpacing(8)
        trow.addWidget(QLabel("Group:"))
        self.group_combo = QComboBox()
        self.group_combo.setEditable(True)  # type a new group or pick existing
        self.group_combo.setInsertPolicy(QComboBox.NoInsert)
        trow.addWidget(self.group_combo)
        # appear empty by default
        self.group_combo.setCurrentIndex(-1)
        self.group_combo.setEditText("")
        if self.group_combo.lineEdit():
            self.group_combo.lineEdit().setPlaceholderText("Group (optional)")

        trow.addSpacing(8)
        trow.addWidget(QLabel("Priority:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        trow.addWidget(self.priority_combo)
        layout.addLayout(trow)

        # Description
        drow = QHBoxLayout()
        drow.addWidget(QLabel("Task Description:"))
        self.task_desc_input = QTextEdit()
        self.task_desc_input.setPlaceholderText("Task description")
        self.task_desc_input.setFixedHeight(110)
        drow.addWidget(self.task_desc_input, 1)
        self.desc_status = QLabel("")
        self.desc_status.setStyleSheet("color:#888;")
        drow.addWidget(self.desc_status)
        layout.addLayout(drow)

        # Due date
        du = QHBoxLayout()
        du.addWidget(QLabel("Due Date:"))
        self.due_date_input = QLineEdit(placeholderText="YYYY-MM-DD")
        du.addWidget(self.due_date_input, 0)
        du.addSpacing(10)
        du.addWidget(QLabel("Format: YYYY-MM-DD"))
        du.addStretch(1)
        layout.addLayout(du)

        # Actions row (left | right). Selection actions live under the list.
        actions = QHBoxLayout()
        self.add_button = QPushButton("➕ Add Task"); self.add_button.clicked.connect(self.add_task)
        self.bulk_button = QPushButton("🧺 Bulk Add"); self.bulk_button.clicked.connect(self.bulk_add_tasks)
        for b in (self.add_button, self.bulk_button):
            b.setProperty("flat", True)
        actions.addWidget(self.add_button)
        actions.addWidget(self.bulk_button)
        actions.addStretch(1)

        self.data_button = QPushButton("📦 Import/Export ▾")
        dm = QMenu(self)
        dm.addAction("📥 Import Tasks", self.import_tasks).setShortcut("Ctrl+I")
        dm.addAction("📤 Export Tasks", self.export_tasks).setShortcut("Ctrl+E")
        self.data_button.setMenu(dm)
        self.data_button.setProperty("flat", True)
        actions.addWidget(self.data_button, 0, Qt.AlignRight)
        layout.addLayout(actions)

        # Filters
        frow = QHBoxLayout()
        frow.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit(placeholderText="Type to filter by title/description...")
        self.search_input.textChanged.connect(self.refresh_tasks)
        frow.addWidget(self.search_input, 1)

        self.group_filter = QComboBox()
        self.group_filter.addItem("All Groups")
        self.group_filter.currentTextChanged.connect(self.refresh_tasks)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Not Completed", "Completed", "Due Today"])
        self.status_filter.currentTextChanged.connect(self.refresh_tasks)

        frow.addSpacing(8)
        frow.addWidget(QLabel("Group:"))
        frow.addWidget(self.group_filter)
        frow.addSpacing(8)
        frow.addWidget(QLabel("Filter:"))
        frow.addWidget(self.status_filter)
        layout.addLayout(frow)

        # List + under-list selection toolbar
        layout.addWidget(QLabel("Your Tasks:"))
        self.task_list = QListWidget()
        self.task_list.itemSelectionChanged.connect(self.show_description)
        self.task_list.itemDoubleClicked.connect(lambda _: self.open_details_popup())
        self.task_list.itemSelectionChanged.connect(self._update_list_actions)
        layout.addWidget(self.task_list, 1)

        # Mini toolbar under the list (selection-specific)
        list_actions = QHBoxLayout()
        self.sel_label = QLabel("No task selected")
        list_actions.addWidget(self.sel_label)
        list_actions.addStretch(1)

        self.complete_button = QPushButton("✔️ Mark Complete")
        self.delete_button   = QPushButton("🗑️ Delete Task")
        for b in (self.complete_button, self.delete_button):
            b.setProperty("flat", True)
        self.complete_button.clicked.connect(self.complete_task)
        self.delete_button.clicked.connect(self.delete_task)
        self.delete_button.setShortcut("Del")

        self.complete_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        list_actions.addWidget(self.complete_button)
        list_actions.addWidget(self.delete_button)
        layout.addLayout(list_actions)

        # Details header with Pop out
        hdr_details = QHBoxLayout()
        hdr_details.addWidget(QLabel("Selected Task Details:"))
        self.details_pop_btn = QPushButton("Pop out")
        self.details_pop_btn.clicked.connect(self.open_details_popup)
        hdr_details.addStretch(1)
        hdr_details.addWidget(self.details_pop_btn)
        layout.addLayout(hdr_details)

        # Scrollable details
        self.task_details = QTextEdit()
        self.task_details.setReadOnly(True)
        self.task_details.setPlaceholderText("Select a task to see its description.")
        self.task_details.setMinimumHeight(110)
        self.task_details.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.task_details)

        self.tabs.addTab(tab, "Tasks")

    # -------------------- Calendar tab --------------------
    def init_calendar_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        top = QHBoxLayout()
        self.cal_toggle_btn = QPushButton("Hide Calendar")
        self.cal_toggle_btn.clicked.connect(self.toggle_calendar_panel)
        self.cal_selected_label = QLabel("Selected: Today")
        top.addWidget(self.cal_toggle_btn)
        top.addStretch(1)
        top.addWidget(self.cal_selected_label)
        v.addLayout(top)

        self.cal_splitter = QSplitter(Qt.Horizontal)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.on_calendar_date_changed)
        self.calendar.selectionChanged.connect(self.on_calendar_selection_changed)
        self.calendar.currentPageChanged.connect(lambda *_: self.refresh_calendar_marks())

        right_box = QWidget()
        right_layout = QVBoxLayout(right_box)
        right_layout.addWidget(QLabel("Tasks on this date:"))
        self.cal_tasks_list = QListWidget()
        right_layout.addWidget(self.cal_tasks_list, 1)

        self.cal_splitter.addWidget(self.calendar)
        self.cal_splitter.addWidget(right_box)
        self.cal_splitter.setStretchFactor(0, 0)
        self.cal_splitter.setStretchFactor(1, 1)

        v.addWidget(self.cal_splitter, 1)

        self.tabs.addTab(tab, "Calendar")

    def toggle_calendar_panel(self):
        if self.calendar.isVisible():
            self.calendar.setVisible(False)
            self.cal_toggle_btn.setText("Show Calendar")
        else:
            self.calendar.setVisible(True)
            self.cal_toggle_btn.setText("Hide Calendar")

    def on_calendar_selection_changed(self):
        self.update_calendar_selected_label()
        self.populate_calendar_day_list()

    def on_calendar_date_changed(self, qdate: QDate):
        self.update_calendar_selected_label(qdate)
        self.populate_calendar_day_list()

    def update_calendar_selected_label(self, qdate: QDate = None):
        qd = qdate if qdate is not None else self.calendar.selectedDate()
        py = date(qd.year(), qd.month(), qd.day())
        if py == date.today():
            self.cal_selected_label.setText("Selected: Today")
        else:
            self.cal_selected_label.setText("Selected: " + py.strftime("%A, %B %d, %Y"))

    def populate_calendar_day_list(self):
        self.cal_tasks_list.clear()
        qd = self.calendar.selectedDate()
        day_iso = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"

        tasks_on_day = [t for t in db.get_tasks(self.user[0]) if t[5] == day_iso]
        if not tasks_on_day:
            self.cal_tasks_list.addItem("No tasks due.")
            return

        for t in tasks_on_day:
            task_id = t[0]
            title = t[2]
            completed = bool(t[4])
            group = self.ucfg["task_groups"].get(str(task_id), "")
            group_badge = f"[{group}] " if group else ""
            prio = self.ucfg["priorities"].get(str(task_id), "low")
            picon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(prio, "🟢")
            status = "✅" if completed else "❌"
            self.cal_tasks_list.addItem(f"{status} {picon} [{task_id}] {group_badge}{title}")

    def refresh_calendar_marks(self):
        cal = self.calendar

        # Palette
        accent_hex = self.cfg.get("accent", "#7AA2F7")
        accent = QColor(accent_hex)
        accent_soft = QColor(accent)
        accent_soft.setAlphaF(0.22)
        accent_strong = QColor(accent)
        accent_strong.setAlphaF(0.38)

        slate = QColor(34, 42, 64, int(255*0.60))   # default tile for in-month
        slate_dim = QColor(34, 42, 64, int(255*0.28))  # out-of-month
        text_main = QColor("#EAF2FF")
        text_dim  = QColor(200, 210, 230, 160)

        # Clear formats for the visible month to soft slate (not black)
        year, month = cal.yearShown(), cal.monthShown()
        first = QDate(year, month, 1)
        days = first.daysInMonth()

        base_fmt = QTextCharFormat()
        base_fmt.setBackground(slate)
        base_fmt.setForeground(text_main)

        for d in range(1, days + 1):
            cal.setDateTextFormat(QDate(year, month, d), base_fmt)

            
        # Iterate a bit around the month range to catch neighbors.
        for delta in (-7, -6, -5, -4, -3, -2, -1, days+1, days+2, days+3, days+4, days+5, days+6, days+7):
            qd = first.addDays(delta)
            fmt = QTextCharFormat()
            fmt.setBackground(slate_dim)
            fmt.setForeground(text_dim)
            cal.setDateTextFormat(qd, fmt)

        # Build marks: any task on date, and if any are incomplete
        marks = {}  # QDate -> (any, has_incomplete)
        for t in db.get_tasks(self.user[0]):
            d = t[5]
            if not d:
                continue
            try:
                dt = datetime.strptime(d, "%Y-%m-%d").date()
            except Exception:
                continue
            qd = QDate(dt.year, dt.month, dt.day)
            any_in_month = (dt.year == year and dt.month == month)
            if not any_in_month:
                continue
            completed = bool(t[4])
            prev_any, prev_incomp = marks.get(qd, (False, False))
            marks[qd] = (True, prev_incomp or (not completed))

        # Apply accent for days with tasks
        for qd, (_any, has_incomplete) in marks.items():
            fmt = QTextCharFormat()
            fmt.setForeground(text_main)
            if has_incomplete:
                fmt.setBackground(accent_strong)   # brighter accent bubble
                fmt.setFontWeight(75)
            else:
                fmt.setBackground(accent_soft)     # subtle tint if all done
                fmt.setFontWeight(63)
            cal.setDateTextFormat(qd, fmt)

        # Highlight "today" with a stronger tile (without neon)
        today = date.today()
        if today.year == year and today.month == month:
            qd = QDate(today.year, today.month, today.day)
            tf = cal.dateTextFormat(qd)
            tf.setBackground(QColor(80, 96, 150, 160))  # bluish ring effect
            tf.setFontWeight(81)
            cal.setDateTextFormat(qd, tf)

        # Keep right pane + label in sync
        self.populate_calendar_day_list()
        self.update_calendar_selected_label()

    # -------------------- Settings tab --------------------
    def init_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("⚙️ Settings"))

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Aurora"])
        current_theme = self.cfg.get("theme", "aurora").lower()
        self.theme_combo.setCurrentIndex(0 if current_theme == "light" else 1 if current_theme == "dark" else 2)
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_row.addWidget(self.theme_combo)

        theme_row.addSpacing(16)
        theme_row.addWidget(QLabel("Accent:"))
        self.accent_combo = QComboBox()
        presets = ["#7AA2F7", "#4caf50", "#ff9800", "#e91e63", "#9c27b0", "Custom…"]
        self.accent_combo.addItems(presets)
        current_accent = self.cfg.get("accent", "#7AA2F7")
        try:
            idx = presets.index(current_accent)
        except ValueError:
            idx = len(presets) - 1
        self.accent_combo.setCurrentIndex(idx)
        self.accent_combo.currentTextChanged.connect(self.on_accent_changed)
        theme_row.addWidget(self.accent_combo)

        theme_row.addStretch(1)
        layout.addLayout(theme_row)

        ginfo = QLabel("Groups help you organize tasks by class or project. "
                       "Create/select one when adding tasks, or use Bulk Add.")
        ginfo.setWordWrap(True)
        layout.addWidget(ginfo)

        row = QHBoxLayout()
        self.reset_button = QPushButton("Reset XP to 0"); self.reset_button.clicked.connect(self.reset_xp)
        self.clear_button = QPushButton("Delete ALL Tasks"); self.clear_button.clicked.connect(self.clear_all_tasks)
        row.addStretch(1)
        row.addWidget(self.reset_button)
        row.addWidget(self.clear_button)
        layout.addLayout(row)

        layout.addStretch(1)
        self.tabs.addTab(tab, "Settings")

    # -------------------- Theme & Accent --------------------
    def on_theme_changed(self, text: str):
        theme = text.lower()
        self.cfg["theme"] = theme
        save_cfg(self.cfg)
        apply_theme_to_app(theme)
        apply_accent_to_window(self, self.cfg.get("accent", "#7AA2F7"))
        apply_aurora_effects_if_needed(self, self.cfg)
        self.refresh_calendar_marks()


    def on_accent_changed(self, text: str):
        color = text
        if text == "Custom…":
            from PyQt5.QtWidgets import QColorDialog
            chosen = QColorDialog.getColor(QColor(self.cfg.get("accent", "#7AA2F7")), self, "Pick Accent Color")
            if chosen.isValid():
                color = chosen.name()
            else:
                return
        self.cfg["accent"] = color
        save_cfg(self.cfg)
        apply_accent_to_window(self, color)
        self.refresh_calendar_marks()


    # -------------------- CRUD --------------------
    def add_task(self):
        title = self.task_input.text().strip()
        description = self.task_desc_input.toPlainText().strip()
        due = self.due_date_input.text().strip()
        prio = self.priority_combo.currentText().lower()
        group = self.group_combo.currentText().strip()

        if not title:
            QMessageBox.warning(self, "Input Error", "Task title cannot be empty."); return
        if len(title) > 100:
            QMessageBox.warning(self, "Input Error", "Task title too long (max 100)."); return
        if len(description) > 1000:
            QMessageBox.warning(self, "Input Error", "Task description too long (max 1000)."); return
        if due and not re.match(r"^\d{4}-\d{2}-\d{2}$", due):
            QMessageBox.warning(self, "Input Error", "Due date must be YYYY-MM-DD."); return

        # insert (allow None for due date)
        try:
            db.add_task(self.user[0], title, description, due or None)
        except Exception as e:
            QMessageBox.critical(self, "Add Task Failed", f"{e}")
            return

        # clear inputs
        self.task_input.clear()
        self.task_desc_input.clear()
        self.due_date_input.clear()
        # reset Group and Priority inputs
        self.group_combo.setCurrentIndex(-1)
        self.group_combo.setEditText("")
        if self.group_combo.lineEdit():
            self.group_combo.lineEdit().setPlaceholderText("Group (optional)")
        self.priority_combo.setCurrentIndex(0)

        # reflect metadata for the new task
        self.refresh_tasks()
        tasks = db.get_tasks(self.user[0])
        if tasks:
            new_task_id = tasks[-1][0]
            self.ucfg["priorities"][str(new_task_id)] = prio
            if group:
                self.ucfg["task_groups"][str(new_task_id)] = group
                if group not in self.ucfg["groups"]:
                    self.ucfg["groups"].append(group)
            save_cfg(self.cfg)
            self.refresh_group_controls()
            # make sure new no-date tasks are visible
            self.status_filter.setCurrentText("All")
            self.refresh_tasks()

    def refresh_tasks(self):
        prev_id = None
        item = getattr(self, "task_list", None)
        if item and item.currentItem():
            try:
                prev_id = int(item.currentItem().text().split("]")[0].split("[")[1])
            except Exception:
                prev_id = None

        self.task_list.clear()
        query = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        filter_mode = self.status_filter.currentText() if hasattr(self, "status_filter") else "All"
        gfilter = self.group_filter.currentText() if hasattr(self, "group_filter") else "All Groups"

        for task in db.get_tasks(self.user[0]):
            # task[0]=id, task[2]=title, task[4]=completed, task[5]=due_date
            task_id = task[0]
            title = task[2]
            completed = bool(task[4])
            due_val = task[5]

            # description for search
            conn = db.get_connection(); cur = conn.cursor()
            cur.execute("SELECT description FROM tasks WHERE id=?", (task_id,))
            rr = cur.fetchone()
            conn.close()
            desc = (rr[0] if rr else "") or ""

            group = self.ucfg["task_groups"].get(str(task_id), "")

            # Filters
            if gfilter != "All Groups" and group != gfilter:
                continue
            if query:
                hay = f"{title}\n{desc}".lower()
                if query not in hay:
                    continue
            if filter_mode == "Completed" and not completed:
                continue
            if filter_mode == "Not Completed" and completed:
                continue
            if filter_mode == "Due Today":
                if not due_val:
                    continue
                try:
                    dt = datetime.strptime(due_val, "%Y-%m-%d").date()
                    if dt != date.today():
                        continue
                except Exception:
                    continue

            prio = self.ucfg["priorities"].get(str(task_id), "low")
            picon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(prio, "🟢")
            status = "✅" if completed else "❌"

            # --- Due date text (show something sensible if empty) ---
            if due_val:
                try:
                    dt = datetime.strptime(due_val, "%Y-%m-%d").date()
                    if dt == date.today():
                        due_txt = " (Due Today!)"
                    else:
                        due_txt = f" (Due: {dt.strftime('%B %d, %Y')})"
                except Exception:
                    due_txt = f" (Due: {due_val})"
            else:
                due_txt = " (No due date)"

            group_badge = f"[{group}] " if group else ""
            txt = f"{status} {picon} [{task_id}] {group_badge}{title}{due_txt}"
            self.task_list.addItem(txt)
            if "Due Today!" in due_txt and not completed:
                self.task_list.item(self.task_list.count() - 1).setForeground(Qt.red)

        self.refresh_user_info()
        self.refresh_calendar_marks()
        self._update_list_actions()

        if prev_id is not None:
            for i in range(self.task_list.count()):
                if f"[{prev_id}]" in self.task_list.item(i).text():
                    self.task_list.setCurrentRow(i)
                    break

    def refresh_user_info(self):
        xp = db.get_user_xp(self.user[0])
        self.user_label.setText(f"XP: {xp}")
        self.level_label.setText(f"Level: {xp // 100}")
        self.level_bar.setValue(xp % 100)
        self.update_streak_label()

    def _selected_task_id(self):
        item = self.task_list.currentItem()
        if not item:
            return None
        try:
            return int(item.text().split("]")[0].split("[")[1])
        except Exception:
            return None

    def complete_task(self):
        task_id = self._selected_task_id()
        if task_id is None:
            return
        db.complete_task(task_id, self.user[0])
        self._log_completion_today()
        self.refresh_tasks()

    def delete_task(self):
        task_id = self._selected_task_id()
        if task_id is None:
            return
        if QMessageBox.question(self, "Delete", "Delete this task?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            db.delete_task(task_id)
            self.ucfg["priorities"].pop(str(task_id), None)
            self.ucfg["task_groups"].pop(str(task_id), None)
            for day, arr in list(self.ucfg.get("reminded", {}).items()):
                self.ucfg["reminded"][day] = [x for x in arr if str(x) != str(task_id)]
            save_cfg(self.cfg)
            self.refresh_tasks()

    def _update_list_actions(self):
        item = self.task_list.currentItem()
        has = item is not None
        self.complete_button.setEnabled(has)
        self.delete_button.setEnabled(has)
        if has:
            try:
                task_id = int(item.text().split("]")[0].split("[")[1])
                self.sel_label.setText(f"Selected: [{task_id}]")
            except Exception:
                self.sel_label.setText("Selected task")
        else:
            self.sel_label.setText("No task selected")

    def show_description(self):
        item = self.task_list.currentItem()
        if not item:
            self.task_details.setPlainText("Select a task to see its description.")
            return
        try:
            task_id = int(item.text().split("]")[0].split("[")[1])
        except Exception:
            self.task_details.setPlainText("Select a task to see its description.")
            return

        conn = db.get_connection(); cur = conn.cursor()
        cur.execute("SELECT title, description, due_date FROM tasks WHERE id=?", (task_id,))
        row = cur.fetchone(); conn.close()
        if not row:
            self.task_details.setPlainText("Select a task to see its description.")
            return

        title, desc, due = row
        if due:
            try:
                dt = datetime.strptime(due, "%Y-%m-%d").date()
                due_txt = "Today" if dt == date.today() else dt.strftime("%B %d, %Y")
            except Exception:
                due_txt = due
        else:
            due_txt = "No due date"

        prio = self.ucfg["priorities"].get(str(task_id), "low").capitalize()
        group = self.ucfg["task_groups"].get(str(task_id), "")
        group_line = f"\nGroup: {group}" if group else ""
        body = f"Title: {title}{group_line}\nPriority: {prio}"
        if due_txt:
            body += f"\nDue Date: {due_txt}"
        body += f"\n\nDescription:\n{desc or '(no description)'}"
        self.task_details.setPlainText(body)

    def open_details_popup(self):
        item = self.task_list.currentItem()
        if not item:
            return
        try:
            task_id = int(item.text().split("]")[0].split("[")[1])
        except Exception:
            return

        conn = db.get_connection(); cur = conn.cursor()
        cur.execute("SELECT title, description, due_date FROM tasks WHERE id=?", (task_id,))
        row = cur.fetchone(); conn.close()
        if not row:
            return
        title, desc, due = row
        prio = self.ucfg["priorities"].get(str(task_id), "low").capitalize()
        group = self.ucfg["task_groups"].get(str(task_id), "")
        if due:
            try:
                dt = datetime.strptime(due, "%Y-%m-%d").date()
                due_txt = "Today" if dt == date.today() else dt.strftime("%B %d, %Y")
            except Exception:
                due_txt = due
        else:
            due_txt = "No due date"
        gline = f"\nGroup: {group}" if group else ""
        content = f"Title: {title}{gline}\nPriority: {prio}"
        if due_txt:
            content += f"\nDue Date: {due_txt}"
        content += f"\n\nDescription:\n{desc or '(no description)'}"

        dlg = QDialog(self); dlg.setWindowTitle(f"Task Details - [{task_id}] {title}")
        v = QVBoxLayout(dlg)
        te = QTextEdit(); te.setReadOnly(True); te.setPlainText(content)
        v.addWidget(te)
        row = QHBoxLayout(); row.addStretch(1)
        btn_copy = QPushButton("Copy"); btn_close = QPushButton("Close")
        row.addWidget(btn_copy); row.addWidget(btn_close); v.addLayout(row)
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(content))
        btn_close.clicked.connect(dlg.close)
        dlg.resize(520, 400)
        dlg.exec_()

    # -------------------- Bulk Add --------------------
    def bulk_add_tasks(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Bulk Add Tasks to a Group")
        vv = QVBoxLayout(dlg)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Group:"))
        group_box = QComboBox()
        group_box.setEditable(True)
        for g in self.ucfg.get("groups", []):
            group_box.addItem(g)
        row1.addWidget(group_box, 1)
        vv.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Due Date (optional):"))
        due_edit = QLineEdit(placeholderText="YYYY-MM-DD (applies to all)")
        row2.addWidget(due_edit, 1)
        vv.addLayout(row2)

        vv.addWidget(QLabel("One task title per line:"))
        titles_edit = QPlainTextEdit()
        titles_edit.setPlaceholderText("Assignment 1\nAssignment 2\nAssignment 3")
        titles_edit.setFixedHeight(180)
        vv.addWidget(titles_edit)

        row3 = QHBoxLayout()
        ok_btn = QPushButton("Add")
        cancel_btn = QPushButton("Cancel")
        row3.addStretch(1)
        row3.addWidget(ok_btn)
        row3.addWidget(cancel_btn)
        vv.addLayout(row3)

        def _accept():
            due_str = due_edit.text().strip()
            if due_str and not re.match(r"^\d{4}-\d{2}-\d{2}$", due_str):
                QMessageBox.warning(dlg, "Input Error", "Due date must be YYYY-MM-DD.")
                return
            lines = [ln.strip() for ln in titles_edit.toPlainText().splitlines()]
            lines = [ln for ln in lines if ln]
            if not lines:
                QMessageBox.warning(dlg, "Input Error", "Enter at least one title.")
                return
            dlg.done(1)

        ok_btn.clicked.connect(_accept)
        cancel_btn.clicked.connect(lambda: dlg.done(0))

        if dlg.exec_() != 1:
            return

        group_name = group_box.currentText().strip()
        due_str = due_edit.text().strip()
        titles = [ln.strip() for ln in titles_edit.toPlainText().splitlines() if ln.strip()]

        imported = 0
        for title in titles:
            db.add_task(self.user[0], title, "", due_str or None)
            imported += 1

        if imported:
            tasks_now = db.get_tasks(self.user[0])
            new_ids = [x[0] for x in tasks_now[-imported:]]
            for new_id in new_ids:
                if group_name:
                    self.ucfg["task_groups"][str(new_id)] = group_name
            if group_name and group_name not in self.ucfg["groups"]:
                self.ucfg["groups"].append(group_name)
            save_cfg(self.cfg)
            self.refresh_group_controls()
            self.refresh_tasks()
            QMessageBox.information(self, "Bulk Add", f"Added {imported} tasks to group '{group_name or 'No Group'}'.")

    # -------------------- Reminders & Streak --------------------
    def check_due_reminders(self):
        today = _today_iso()
        reminded_today = set(map(str, self.ucfg.get("reminded", {}).get(today, [])))
        to_add = []

        for task in db.get_tasks(self.user[0]):
            task_id = str(task[0])
            completed = bool(task[4])
            due = task[5]
            if completed or not due:
                continue
            try:
                dt = datetime.strptime(due, "%Y-%m-%d").date()
            except Exception:
                continue

            if dt == date.today() and task_id not in reminded_today:
                title = task[2]
                group = self.ucfg["task_groups"].get(task_id, "")
                gtxt = f" [{group}]" if group else ""
                QMessageBox.information(self, "Reminder", f"⚠️ '{title}'{gtxt} is due today.")
                to_add.append(task_id)

        if to_add:
            self.ucfg.setdefault("reminded", {})
            self.ucfg.setdefault("reminded", {}).setdefault(today, [])
            self.ucfg["reminded"][today].extend(to_add)
            save_cfg(self.cfg)

    def _log_completion_today(self):
        today = _today_iso()
        logs = self.ucfg.get("completion_log", [])
        if today not in logs:
            logs.append(today)
            self.ucfg["completion_log"] = logs
            save_cfg(self.cfg)

    def update_streak_label(self):
        logs = sorted(set(self.ucfg.get("completion_log", [])))
        if not logs:
            self.streak_label.setText("🔥 Streak: 0")
            return
        streak = 0
        cur = date.today()
        logset = set(logs)
        while cur.isoformat() in logset:
            streak += 1
            cur -= timedelta(days=1)
        self.streak_label.setText(f"🔥 Streak: {streak}")

    # -------------------- Export / Import --------------------
    def export_tasks(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Tasks", "tasks_export.json", "JSON Files (*.json)")
        if not path:
            return
        tasks_out = []
        for task in db.get_tasks(self.user[0]):
            task_id = task[0]
            conn = db.get_connection(); cur = conn.cursor()
            cur.execute("SELECT description FROM tasks WHERE id=?", (task_id,))
            rr = cur.fetchone()
            conn.close()
            desc = (rr[0] if rr else "") or ""
            tasks_out.append({
                "id": task_id,
                "title": task[2],
                "description": desc,
                "completed": bool(task[4]),
                "due_date": task[5],
                "priority": self.ucfg["priorities"].get(str(task_id), "low"),
                "group": self.ucfg["task_groups"].get(str(task_id), "")
            })

        data = {
            "user": {"id": self.user[0], "username": self.user[1]},
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "tasks": tasks_out,
            "groups": self.ucfg.get("groups", [])
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            QMessageBox.information(self, "Export", "Tasks exported successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export tasks:\n{e}")

    def import_tasks(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Tasks", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Invalid JSON file:\n{e}")
            return

        tasks = data.get("tasks", [])
        if not isinstance(tasks, list):
            QMessageBox.warning(self, "Import Error", "No tasks found in file.")
            return

        imported = 0
        groups_from_file = set(data.get("groups", []))

        sanitized = []
        for t in tasks:
            title = (t.get("title") or "").strip()
            desc = (t.get("description") or "").strip()
            due = (t.get("due_date") or None)
            prio = (t.get("priority") or "low").lower()
            grp = (t.get("group") or "").strip()
            if not title:
                continue
            if due and not re.match(r"^\d{4}-\d{2}-\d{2}$", due):
                due = None
            sanitized.append((title, desc, due, prio, grp))

        for title, desc, due, prio, grp in sanitized:
            db.add_task(self.user[0], title, desc, due)
            imported += 1

        if imported:
            tasks_now = db.get_tasks(self.user[0])
            new_ids = [x[0] for x in tasks_now[-imported:]]
            for (new_id, (title, desc, due, prio, grp)) in zip(new_ids, sanitized):
                self.ucfg["priorities"][str(new_id)] = prio
                if grp:
                    self.ucfg["task_groups"][str(new_id)] = grp
                    groups_from_file.add(grp)

            for g in groups_from_file:
                if g and g not in self.ucfg["groups"]:
                    self.ucfg["groups"].append(g)

            save_cfg(self.cfg)
            self.refresh_group_controls()
            self.refresh_tasks()
            QMessageBox.information(self, "Import", f"Imported {imported} tasks.")
        else:
            QMessageBox.information(self, "Import", "Nothing to import.")

    # -------------------- Settings actions --------------------
    def reset_xp(self):
        if QMessageBox.question(
            self, "Reset XP", "Reset your XP to 0?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            conn = db.get_connection(); cur = conn.cursor()
            cur.execute("UPDATE users SET xp = 0 WHERE id=?", (self.user[0],))
            conn.commit(); conn.close()
            self.refresh_user_info()
            self.refresh_calendar_marks()

    def clear_all_tasks(self):
        if QMessageBox.question(
            self, "Delete All Tasks", "Delete ALL your tasks?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            conn = db.get_connection(); cur = conn.cursor()
            cur.execute("DELETE FROM tasks WHERE user_id=?", (self.user[0],))
            conn.commit(); conn.close()
            self.refresh_tasks()

    # -------------------- Helpers --------------------
    def refresh_group_controls(self):
        # Add-task combo (blank by default; don't preserve previous text)
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        for g in self.ucfg.get("groups", []):
            self.group_combo.addItem(g)
        self.group_combo.setEditable(True)
        self.group_combo.setInsertPolicy(QComboBox.NoInsert)
        self.group_combo.setCurrentIndex(-1)
        self.group_combo.setEditText("")
        if self.group_combo.lineEdit():
            self.group_combo.lineEdit().setPlaceholderText("Group (optional)")
        self.group_combo.blockSignals(False)

        # Filter combo (preserve current selection)
        sel = self.group_filter.currentText() if hasattr(self, "group_filter") else "All Groups"
        self.group_filter.blockSignals(True)
        self.group_filter.clear()
        self.group_filter.addItem("All Groups")
        for g in self.ucfg.get("groups", []):
            self.group_filter.addItem(g)
        idx = 0
        for i in range(self.group_filter.count()):
            if self.group_filter.itemText(i) == sel:
                idx = i
                break
        self.group_filter.setCurrentIndex(idx)
        self.group_filter.blockSignals(False)

    def closeEvent(self, e):
        super().closeEvent(e)
