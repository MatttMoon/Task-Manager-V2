# ui/calendar_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QListWidget, QCalendarWidget
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QTextCharFormat, QColor, QFont
from datetime import datetime, date
from db import database as db
from core.models import Task, task_from_row



# -------------------- Build tab --------------------
def init_calendar_tab(window):
    """Builds the Calendar tab UI and attaches it to the main window's tabs."""
    tab = QWidget()
    v = QVBoxLayout(tab)

    # Top row: toggle + selected label
    top = QHBoxLayout()
    window.cal_toggle_btn = QPushButton("Hide Calendar")
    window.cal_toggle_btn.clicked.connect(lambda: toggle_calendar_panel(window))
    window.cal_selected_label = QLabel("Selected: Today")
    top.addWidget(window.cal_toggle_btn)
    top.addStretch(1)
    top.addWidget(window.cal_selected_label)
    v.addLayout(top)

    # Splitter: calendar (left) | list (right)
    window.cal_splitter = QSplitter(Qt.Horizontal)

    window.calendar = QCalendarWidget()
    window.calendar.setGridVisible(True)
    # ✅ Show weekday header; hide week numbers (no white gutter)
    window.calendar.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
    window.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
    window.calendar.setFirstDayOfWeek(Qt.Monday)

    window.calendar.clicked.connect(lambda qd: on_calendar_date_changed(window, qd))
    window.calendar.selectionChanged.connect(lambda: on_calendar_selection_changed(window))
    window.calendar.currentPageChanged.connect(lambda *_: refresh_calendar_marks(window))

    right_box = QWidget()
    right_layout = QVBoxLayout(right_box)
    right_layout.addWidget(QLabel("Tasks on this date:"))
    window.cal_tasks_list = QListWidget()
    right_layout.addWidget(window.cal_tasks_list, 1)

    window.cal_splitter.addWidget(window.calendar)
    window.cal_splitter.addWidget(right_box)
    window.cal_splitter.setStretchFactor(0, 0)
    window.cal_splitter.setStretchFactor(1, 1)

    # Slightly shrink calendar panel by default
    window.cal_splitter.setSizes([350, 9999])

    v.addWidget(window.cal_splitter, 1)
    window.tabs.addTab(tab, "Calendar")

    # Initial paint / sync
    refresh_calendar_marks(window)
    update_calendar_selected_label(window)
    populate_calendar_day_list(window)


# -------------------- Handlers --------------------
def toggle_calendar_panel(window):
    if window.calendar.isVisible():
        window.calendar.setVisible(False)
        window.cal_toggle_btn.setText("Show Calendar")
    else:
        window.calendar.setVisible(True)
        window.cal_toggle_btn.setText("Hide Calendar")


def on_calendar_selection_changed(window):
    update_calendar_selected_label(window)
    populate_calendar_day_list(window)


def on_calendar_date_changed(window, qdate: QDate):
    update_calendar_selected_label(window, qdate)
    populate_calendar_day_list(window)


def update_calendar_selected_label(window, qdate: QDate = None):
    qd = qdate if qdate is not None else window.calendar.selectedDate()
    py = date(qd.year(), qd.month(), qd.day())
    if py == date.today():
        window.cal_selected_label.setText("Selected: Today")
    else:
        window.cal_selected_label.setText("Selected: " + py.strftime("%A, %B %d, %Y"))


# -------------------- Data helpers --------------------
def _load_tasks(window) -> list[Task]:
    """Read tasks from DB and return Task objects (safe on errors)."""
    try:
        rows = db.get_tasks(window.user[0]) or []
    except Exception:
        return []
    tasks: list[Task] = []
    for r in rows:
        try:
            tasks.append(task_from_row(r))
        except Exception:
            continue
    return tasks



def _user_cfg(window):
    # window.ucfg may not exist in some app states
    return getattr(window, "ucfg", {}) or {}


def populate_calendar_day_list(window):
    window.cal_tasks_list.clear()
    qd = window.calendar.selectedDate()
    day_iso = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"

    tasks_on_day = [t for t in db.get_tasks(window.user[0]) if t.due_date and t.due_date.isoformat() == day_iso]

    if not tasks_on_day:
        window.cal_tasks_list.addItem("No tasks due.")
        return

    ucfg = _user_cfg(window)
    tgroups = ucfg.get("task_groups", {}) or {}
    pris = ucfg.get("priorities", {}) or {}

    for t in tasks_on_day:
        group = tgroups.get(str(t.id), "")
        group_badge = f"[{group}] " if group else ""

        prio = (pris.get(str(t.id)) or "low").lower()
        picon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(prio, "🟢")

        status = "✅" if t.completed else "❌"
        window.cal_tasks_list.addItem(f"{status} {picon} [{t.id}] {group_badge}{t.title}")


# -------------------- Calendar marking --------------------
def refresh_calendar_marks(window):
    """
    White calendar for all themes (handled by QSS).
    Here we only set readable text colors and light cues.
    """
    cal = window.calendar

    # wipe any stale formats
    cal.setDateTextFormat(QDate(), QTextCharFormat())
    for dow in (Qt.Monday, Qt.Tuesday, Qt.Wednesday, Qt.Thursday,
                Qt.Friday, Qt.Saturday, Qt.Sunday):
        cal.setWeekdayTextFormat(dow, QTextCharFormat())

    # text palette (works on white calendar)
    fg_norm    = QColor("#1A1F2B")
    fg_header  = QColor("#1A1F2B")
    fg_weekend = QColor("#CC0000")
    fg_today   = QColor("#000000")

    # weekday labels (Mon..Sun)
    header_fmt = QTextCharFormat()
    header_fmt.setForeground(fg_header)
    for dow in (Qt.Monday, Qt.Tuesday, Qt.Wednesday, Qt.Thursday, Qt.Friday):
        cal.setWeekdayTextFormat(dow, header_fmt)
    sat_fmt = QTextCharFormat(header_fmt); sat_fmt.setForeground(fg_weekend)
    sun_fmt = QTextCharFormat(header_fmt); sun_fmt.setForeground(fg_weekend)
    cal.setWeekdayTextFormat(Qt.Saturday, sat_fmt)
    cal.setWeekdayTextFormat(Qt.Sunday, sun_fmt)

    # current month days
    year, month = cal.yearShown(), cal.monthShown()
    first = QDate(year, month, 1)
    days = first.daysInMonth()
    base = QTextCharFormat(); base.setForeground(fg_norm)
    for d in range(1, days + 1):
        cal.setDateTextFormat(QDate(year, month, d), base)

    # weekends inside this month -> red text
    for d in range(1, days + 1):
        qd = QDate(year, month, d)
        if qd.dayOfWeek() in (6, 7):
            wf = cal.dateTextFormat(qd)
            wf.setForeground(fg_weekend)
            cal.setDateTextFormat(qd, wf)

    # today -> stronger/black text
    today = date.today()
    if today.year == year and today.month == month:
        qd = QDate(today.year, today.month, today.day)
        tf = cal.dateTextFormat(qd)
        tf.setForeground(fg_today)
        tf.setFontWeight(QFont.DemiBold)
        cal.setDateTextFormat(qd, tf)

    # due-date cue (text-only; no backgrounds)
        # due-date cue (text-only; no backgrounds) — now using Task objects
    accent_hex = (getattr(window, "cfg", {}) or {}).get("accent", "#7AA2F7")
    accent_fg  = QColor(accent_hex)

    marks: dict[QDate, bool] = {}  # QDate -> any incomplete on that day?

    for t in _load_tasks(window):
        dt = t.due_date
        if not dt or dt.year != year or dt.month != month:
            continue
        qd = QDate(dt.year, dt.month, dt.day)
        # mark true if ANY task on that date is incomplete
        marks[qd] = marks.get(qd, False) or (not t.completed)

    for qd, has_incomplete in marks.items():
        ff = cal.dateTextFormat(qd)
        if has_incomplete:
            ff.setFontWeight(QFont.DemiBold)
            ff.setForeground(accent_fg)
        else:
            ff.setFontWeight(QFont.Normal)
        cal.setDateTextFormat(qd, ff)
    accent_hex = (getattr(window, "cfg", {}) or {}).get("accent", "#7AA2F7")
    accent_fg  = QColor(accent_hex)
    marks = {}
    for task in (db.get_tasks(window.user[0]) or []):
        dstr = task[5]
        if not dstr:
            continue
        try:
            dt = datetime.strptime(dstr, "%Y-%m-%d").date()
        except Exception:
            continue
        if dt.year == year and dt.month == month:
            qd = QDate(dt.year, dt.month, dt.day)
            marks[qd] = marks.get(qd, False) or (not bool(task[4]))

    for qd, has_incomplete in marks.items():
        ff = cal.dateTextFormat(qd)
        if has_incomplete:
            ff.setFontWeight(QFont.DemiBold)
            ff.setForeground(accent_fg)
        cal.setDateTextFormat(qd, ff)
