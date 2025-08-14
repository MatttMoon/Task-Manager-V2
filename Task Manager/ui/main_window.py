# ui/main_window.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit,
    QListWidget, QMessageBox, QTabWidget, QHBoxLayout, QComboBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime, date
from db import database as db
import re, json, os, threading

# SpeechRecognition is optional; app still runs without it.
try:
    import speech_recognition as sr
    VOICE_OK = True
except Exception:
    VOICE_OK = False

CONFIG_FILE = "app_settings.json"


def _load_cfg():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f) or {}
    except Exception:
        pass
    return {}


def _save_cfg(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


class MainWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user  # (id, username, xp)
        self.setWindowTitle("Task Manager with XP System")
        self.resize(760, 600)

        # ---- settings / persistence ----
        self.cfg = _load_cfg()
        self.mic_index = self.cfg.get("mic_device_index", None)  # int, or None for system default

        # ---- speech state (lazy init) ----
        self._r = None              # sr.Recognizer
        self._mic = None            # sr.Microphone bound to selected device
        self._bg_stop = None        # stop handle from listen_in_background
        self._listen_timer = None   # watchdog QTimer

        # ---- tabs / layout ----
        self.tabs = QTabWidget(self)
        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

        self.init_task_tab()
        self.init_settings_tab()

        # stop SR threads cleanly when app quits
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self._shutdown_voice)

        self.refresh_tasks()

    # =========================
    # Task tab
    # =========================
    def init_task_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # header
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("User Progress:"))
        self.user_label = QLabel("XP: 0")
        self.level_label = QLabel("Level: 0")
        hdr.addStretch(1)
        hdr.addWidget(self.user_label); hdr.addSpacing(10); hdr.addWidget(self.level_label)
        layout.addLayout(hdr)

        # title + mic
        trow = QHBoxLayout()
        trow.addWidget(QLabel("Task Title:"))
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter task title")
        self.task_input.setToolTip("Required. Max 100 characters.")
        trow.addWidget(self.task_input, 1)

        self.title_mic_btn = QPushButton("🎤")
        self.title_mic_btn.setFixedWidth(36)
        self.title_mic_btn.setFocusPolicy(Qt.NoFocus)
        self.title_mic_btn.setToolTip("Click, then speak the task title")
        self.title_mic_btn.clicked.connect(self.mic_fill_title)
        trow.addWidget(self.title_mic_btn)

        self.title_status = QLabel("")
        self.title_status.setStyleSheet("color:#888;")
        trow.addWidget(self.title_status)
        layout.addLayout(trow)

        # description + mic
        drow = QHBoxLayout()
        drow.addWidget(QLabel("Task Description:"))
        self.task_desc = QTextEdit()
        self.task_desc.setPlaceholderText("Task description")
        self.task_desc.setFixedHeight(110)
        drow.addWidget(self.task_desc, 1)

        self.desc_mic_btn = QPushButton("🎤")
        self.desc_mic_btn.setFixedWidth(36)
        self.desc_mic_btn.setFocusPolicy(Qt.NoFocus)
        self.desc_mic_btn.setToolTip("Click, then speak the task description")
        self.desc_mic_btn.clicked.connect(self.mic_fill_description)
        drow.addWidget(self.desc_mic_btn)

        self.desc_status = QLabel("")
        self.desc_status.setStyleSheet("color:#888;")
        drow.addWidget(self.desc_status)
        layout.addLayout(drow)

        # due date (manual)
        du = QHBoxLayout()
        du.addWidget(QLabel("Due Date:"))
        self.due_date_input = QLineEdit()
        self.due_date_input.setPlaceholderText("YYYY-MM-DD")
        du.addWidget(self.due_date_input, 0)
        du.addSpacing(10)
        du.addWidget(QLabel("Format: YYYY-MM-DD"))
        du.addStretch(1)
        layout.addLayout(du)

        # action buttons
        btns = QHBoxLayout()
        self.add_button = QPushButton("➕ Add Task"); self.add_button.clicked.connect(self.add_task)
        self.complete_button = QPushButton("✔️ Mark Complete"); self.complete_button.clicked.connect(self.complete_task)
        self.delete_button = QPushButton("🗑️ Delete Task"); self.delete_button.clicked.connect(self.delete_task)
        btns.addStretch(1); btns.addWidget(self.add_button); btns.addWidget(self.complete_button); btns.addWidget(self.delete_button)
        layout.addLayout(btns)

        # list + details
        layout.addWidget(QLabel("Your Tasks:"))
        self.task_list = QListWidget()
        self.task_list.itemSelectionChanged.connect(self.show_description)
        layout.addWidget(self.task_list, 1)

        layout.addWidget(QLabel("Selected Task Details:"))
        self.task_description_label = QLabel("Select a task to see its description.")
        self.task_description_label.setWordWrap(True)
        self.task_description_label.setFixedHeight(94)
        layout.addWidget(self.task_description_label)

        self.tabs.addTab(tab, "Tasks")

    # =========================
    # Settings tab (Microphone picker)
    # =========================
    def init_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("⚙️ Settings"))

        # mic picker row
        mic_row = QHBoxLayout()
        mic_row.addWidget(QLabel("Microphone:"))
        self.mic_combo = QComboBox()
        self.mic_refresh_btn = QPushButton("Refresh")
        self.mic_save_btn = QPushButton("Save")
        self.mic_refresh_btn.clicked.connect(self.populate_mic_combo)
        self.mic_save_btn.clicked.connect(self.save_mic_selection)
        mic_row.addWidget(self.mic_combo, 1)
        mic_row.addWidget(self.mic_refresh_btn)
        mic_row.addWidget(self.mic_save_btn)
        layout.addLayout(mic_row)

        # reset/clear
        row = QHBoxLayout()
        self.reset_button = QPushButton("Reset XP to 0"); self.reset_button.clicked.connect(self.reset_xp)
        self.clear_button = QPushButton("Delete ALL Tasks"); self.clear_button.clicked.connect(self.clear_all_tasks)
        row.addStretch(1); row.addWidget(self.reset_button); row.addWidget(self.clear_button)
        layout.addLayout(row)

        layout.addStretch(1)
        self.tabs.addTab(tab, "Settings")

        self.populate_mic_combo()

    def populate_mic_combo(self):
        self.mic_combo.clear()
        if not VOICE_OK:
            self.mic_combo.addItem("SpeechRecognition not installed", -1)
            self.mic_combo.setEnabled(False)
            self.mic_refresh_btn.setEnabled(False)
            self.mic_save_btn.setEnabled(False)
            return
        try:
            names = sr.Microphone.list_microphone_names() or []
        except Exception:
            names = []

        if not names:
            self.mic_combo.addItem("No input devices found", -1)
            self.mic_combo.setEnabled(False)
            self.mic_save_btn.setEnabled(False)
            return

        self.mic_combo.setEnabled(True)
        self.mic_save_btn.setEnabled(True)
        for i, name in enumerate(names):
            self.mic_combo.addItem(f"[{i}] {name}", i)

        if isinstance(self.mic_index, int) and 0 <= self.mic_index < len(names):
            idx = self.mic_combo.findData(self.mic_index)
            if idx != -1:
                self.mic_combo.setCurrentIndex(idx)

    def save_mic_selection(self):
        data = self.mic_combo.currentData()
        if isinstance(data, int) and data >= 0:
            self.mic_index = data
            self.cfg["mic_device_index"] = data
            _save_cfg(self.cfg)
            # if already initialized, rebind live
            if VOICE_OK and self._mic is not None:
                try:
                    self._mic = sr.Microphone(device_index=self.mic_index)
                except Exception:
                    pass
            QMessageBox.information(self, "Microphone Saved", f"Using input device index {data}.")
        else:
            QMessageBox.warning(self, "Microphone", "Please select a valid input device.")

    # =========================
    # CRUD + UI refresh
    # =========================
    def add_task(self):
        title = self.task_input.text().strip()
        description = self.task_desc.toPlainText().strip()
        due = self.due_date_input.text().strip()

        if not title:
            QMessageBox.warning(self, "Input Error", "Task title cannot be empty."); return
        if len(title) > 100:
            QMessageBox.warning(self, "Input Error", "Task title too long (max 100)."); return
        if len(description) > 1000:
            QMessageBox.warning(self, "Input Error", "Task description too long (max 1000)."); return
        if due and not re.match(r"^\d{4}-\d{2}-\d{2}$", due):
            QMessageBox.warning(self, "Input Error", "Due date must be YYYY-MM-DD."); return

        db.add_task(self.user[0], title, description, due or None)
        self.task_input.clear(); self.task_desc.clear(); self.due_date_input.clear()
        self.refresh_tasks()

    def refresh_tasks(self):
        self.task_list.clear()
        for task in db.get_tasks(self.user[0]):
            # (id, user_id, title, description, complete, due_date)
            status = "✅" if task[4] else "❌"
            due = ""
            if task[5]:
                try:
                    dt = datetime.strptime(task[5], "%Y-%m-%d").date()
                    due = " (Due Today!)" if dt == date.today() else f" (Due: {dt.strftime('%B %d, %Y')})"
                except Exception:
                    due = f" (Due: {task[5]})"
            txt = f"{status} [{task[0]}] {task[2]}{due}"
            self.task_list.addItem(txt)
            if "Due Today!" in due:
                self.task_list.item(self.task_list.count()-1).setForeground(Qt.red)
        self.refresh_user_info()

    def refresh_user_info(self):
        xp = db.get_user_xp(self.user[0])
        self.user_label.setText(f"XP: {xp}")
        self.level_label.setText(f"Level: {xp // 100}")

    def complete_task(self):
        item = self.task_list.currentItem()
        if not item: return
        task_id = int(item.text().split("]")[0].split("[")[1])
        db.complete_task(task_id, self.user[0])
        self.refresh_tasks()

    def delete_task(self):
        item = self.task_list.currentItem()
        if not item: return
        task_id = int(item.text().split("]")[0].split("[")[1])
        if QMessageBox.question(self, "Delete", "Delete this task?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            db.delete_task(task_id)
            self.refresh_tasks()

    def show_description(self):
        item = self.task_list.currentItem()
        if not item:
            self.task_description_label.setText("Select a task to see its description."); return
        try:
            task_id = int(item.text().split("]")[0].split("[")[1])
        except Exception:
            self.task_description_label.setText("Select a task to see its description."); return

        conn = db.get_connection(); cur = conn.cursor()
        cur.execute("SELECT title, description, due_date FROM tasks WHERE id=?", (task_id,))
        row = cur.fetchone(); conn.close()
        if not row:
            self.task_description_label.setText("Select a task to see its description."); return
        title, desc, due = row
        due_txt = ""
        if due:
            try:
                dt = datetime.strptime(due, "%Y-%m-%d").date()
                due_txt = "\nDue Date: Today" if dt == date.today() else f"\nDue Date: {dt.strftime('%B %d, %Y')}"
            except Exception:
                due_txt = f"\nDue Date: {due}"
        self.task_description_label.setText(f"Title: {title}\n\nDescription:\n{desc}{due_txt}")

    # settings actions
    def reset_xp(self):
        if QMessageBox.question(self, "Reset XP", "Reset your XP to 0?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            conn = db.get_connection(); cur = conn.cursor()
            cur.execute("UPDATE users SET xp = 0 WHERE id=?", (self.user[0],))
            conn.commit(); conn.close()
            self.refresh_user_info()

    def clear_all_tasks(self):
        if QMessageBox.question(self, "Delete All Tasks", "Delete ALL your tasks?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            conn = db.get_connection(); cur = conn.cursor()
            cur.execute("DELETE FROM tasks WHERE user_id=?", (self.user[0],))
            conn.commit(); conn.close()
            self.refresh_tasks()

    # =========================
    # Voice helpers
    # =========================
    def _init_voice(self):
        """Lazy-init recognizer and microphone. Calibrate quickly once."""
        if not VOICE_OK:
            raise RuntimeError("SpeechRecognition not available")

        if self._r is None:
            self._r = sr.Recognizer()
            self._r.dynamic_energy_threshold = False
            self._r.energy_threshold = 500
            self._r.pause_threshold = 0.7
            self._r.non_speaking_duration = 0.3

        if self._mic is None:
            self._mic = sr.Microphone(device_index=self.mic_index)
            try:
                with self._mic as src:
                    # short ambient calibration prevents “listening forever”
                    self._r.adjust_for_ambient_noise(src, duration=0.25)
            except Exception:
                pass

    def _ui_listen_state(self, btn: QPushButton, lbl: QLabel, on: bool):
        if on:
            btn.setText("●"); btn.setEnabled(False)
            btn.setStyleSheet("background:#e74c3c; color:white;")
            lbl.setText("listening…")
        else:
            btn.setText("🎤"); btn.setEnabled(True)
            btn.setStyleSheet("")
            lbl.setText("")

    def _stop_bg_ui(self, btn, lbl):
        # stop listener (quick) and reset UI on the UI thread
        if self._bg_stop:
            try:
                self._bg_stop(wait_for_stop=False)
            except Exception:
                pass
            self._bg_stop = None
        if self._listen_timer and self._listen_timer.isActive():
            self._listen_timer.stop()
        self._listen_timer = None
        self._ui_listen_state(btn, lbl, False)

    def _start_bg(self, btn, lbl, setter, hard_cap_ms=9000):
        try:
            self._init_voice()
        except Exception:
            self._ui_listen_state(btn, lbl, False); return

        # stop any previous listener
        if self._bg_stop:
            self._stop_bg_ui(btn, lbl)

        self._ui_listen_state(btn, lbl, True)

        def _callback(recognizer, audio):
            def _recognize():
                text = None
                try:
                    text = recognizer.recognize_google(audio, language="en-US").strip()
                except Exception:
                    text = None
                # marshal back to UI thread
                QTimer.singleShot(0, lambda: (setter(text) if text else None, self._stop_bg_ui(btn, lbl)))
            threading.Thread(target=_recognize, daemon=True).start()

        try:
            self._bg_stop = self._r.listen_in_background(self._mic, _callback)
        except Exception:
            self._bg_stop = None
            self._ui_listen_state(btn, lbl, False)
            return

        # watchdog so the UI never gets stuck
        self._listen_timer = QTimer(self)
        self._listen_timer.setSingleShot(True)
        self._listen_timer.timeout.connect(lambda: self._stop_bg_ui(btn, lbl))
        self._listen_timer.start(hard_cap_ms)

    # mic handlers
    def mic_fill_title(self):
        self.task_input.setFocus()
        self._start_bg(self.title_mic_btn, self.title_status,
                       lambda t: self.task_input.setText(t) if t else None,
                       hard_cap_ms=9000)

    def mic_fill_description(self):
        self.task_desc.setFocus()
        self._start_bg(self.desc_mic_btn, self.desc_status,
                       lambda t: self.task_desc.setPlainText(t) if t else None,
                       hard_cap_ms=11000)

    # clean shutdown (join SR worker)
    def _shutdown_voice(self):
        if self._bg_stop:
            try:
                self._bg_stop(wait_for_stop=True)  # join thread on exit
            except Exception:
                pass
            self._bg_stop = None
        if self._listen_timer and self._listen_timer.isActive():
            self._listen_timer.stop()
        self._listen_timer = None

    def closeEvent(self, e):
        self._shutdown_voice()
        super().closeEvent(e)
