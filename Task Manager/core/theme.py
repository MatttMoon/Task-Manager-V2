# core/theme.py
from PyQt5.QtWidgets import QApplication, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor

# --- public helpers you will import in main_window.py ---

def apply_theme_to_app(theme: str):
    """Apply one of: 'aurora', 'dark', 'light' to the whole app."""
    app = QApplication.instance()
    if not app:
        return
    t = (theme or "aurora").lower()
    if t == "aurora":
        app.setStyleSheet(_aurora_qss())
    elif t == "dark":
        app.setStyleSheet(_dark_qss())
    else:
        app.setStyleSheet(_light_qss())

def apply_accent_to_window(window, hex_color: str):
    """Accent border/selection colors that work across themes."""
    accent = hex_color or "#7AA2F7"
    window.setStyleSheet(f"""
    QLineEdit:focus, QTextEdit:focus, QListWidget:focus {{ border: 1px solid {accent}; }}
    QListWidget::item:selected {{ background: {accent}; color: white; }}
    QPushButton:hover {{ border: 1px solid {accent}; }}
    QProgressBar::chunk {{ background-color: {accent}; }}
    """)

def apply_aurora_effects_if_needed(window, cfg: dict):
    """Add soft glow on widgets if the 'Aurora' theme is active."""
    if (cfg or {}).get("theme", "aurora").lower() != "aurora":
        return
    _apply_aurora_effects(window)

# --- internal: the soft glow used by Aurora ---
def _apply_aurora_effects(window):
    def glow(w, radius=24, alpha=0.22):
        eff = QGraphicsDropShadowEffect(window)
        eff.setColor(QColor(122, 162, 247, int(alpha * 255)))
        eff.setBlurRadius(radius)
        eff.setOffset(0, 6)
        w.setGraphicsEffect(eff)

    # try to glow these widgets if they exist on the window
    for name in [
        "task_list", "task_details", "search_input", "due_date_input",
        "level_bar", "calendar", "cal_tasks_list"
    ]:
        w = getattr(window, name, None)
        if w:
            glow(w)

# --- THEME STYLE SHEETS (QSS) ---
# IMPORTANT: copy your three functions from main_window.py and paste
# them here, replacing the three stubs below. keep the contents identical.

def _aurora_qss() -> str:
        # Aurora: glassy cards on blue-violet gradient (QSS-safe)
        return """
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #0f1424, stop:0.5 #151a2d, stop:1 #1b213a);
            color: #EAF2FF; font-size: 14px;
        }
        QLabel { color: #EAF2FF; }

        /* Glass cards */
        QLineEdit, QTextEdit, QListWidget, QComboBox, QCalendarWidget,
        QTabWidget::pane, QProgressBar {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 12px;
            padding: 6px;
        }
        QCalendarWidget QWidget { background: transparent; color: #EAF2FF; }

        /* Inputs focus ring (just border color) */
        QLineEdit:focus, QTextEdit:focus, QListWidget:focus, QComboBox:focus {
            border: 1px solid #7AA2F7;
        }

        /* Buttons: gradient; no CSS filters */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #4A5EEA, stop:1 #6ED3FF);
            color: #ffffff; border: 0; border-radius: 10px; padding: 7px 12px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #5567f0, stop:1 #7ae0ff);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #3d54d9, stop:1 #55c7f5);
        }

        /* Secondary/chip look when property flat=true */
        QPushButton[flat="true"] {
            background: rgba(255,255,255,0.08); color: #EAF2FF;
            border: 1px solid rgba(255,255,255,0.12);
        }
        QPushButton[flat="true"]:hover {
            border: 1px solid rgba(122,162,247,0.45);
            background: rgba(122,162,247,0.12);
        }
        QPushButton[flat="true"]:pressed {
            background: rgba(122,162,247,0.22);
        }

        /* Tabs */
        QTabBar::tab {
            background: rgba(255,255,255,0.08);
            color: #DDE9FF; padding: 8px 14px;
            border: 1px solid rgba(255,255,255,0.12);
            border-top-left-radius: 10px; border-top-right-radius: 10px;
            margin-right: 6px;
        }
        QTabBar::tab:selected {
            background: rgba(122,162,247,0.18); color: #FFFFFF;
            border: 1px solid rgba(122,162,247,0.35);
        }

        /* Lists & selection */
        QListWidget::item { padding: 6px; margin: 3px 4px; border-radius: 8px; }
        QListWidget::item:selected { background: rgba(122,162,247,0.35); color: #FFFFFF; }

        /* Combo popup */
        QComboBox QAbstractItemView {
            background: rgba(20,25,45,0.98);
            color: #EAF2FF; border: 1px solid rgba(255,255,255,0.12);
            selection-background-color: rgba(122,162,247,0.35);
        }

        /* Progress */
        QProgressBar { text-align: center; height: 18px; }
        QProgressBar::chunk {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #8A7DFF, stop:1 #4AD0FF);
            border-radius: 8px;
        }

        /* Calendar tweaks (Aurora) */
        QCalendarWidget {
            background: transparent;
            color: #EAF2FF;
        }
        QCalendarWidget QTableView {
            background: rgba(255,255,255,0.05); /* soft slate instead of black */
            alternate-background-color: transparent;
            outline: 0;
        }
        QCalendarWidget QTableView:item {
            padding: 6px;
        }
        QCalendarWidget QToolButton {
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 8px;
            padding: 4px 10px;
        }
        QCalendarWidget QToolButton:hover {
            background: rgba(255,255,255,0.16);
        }
        QCalendarWidget QMenu {
            background: rgba(20,25,45,0.98);
            color: #EAF2FF;
            border: 1px solid rgba(255,255,255,0.12);
        }
        QCalendarWidget QSpinBox, 
        QCalendarWidget QComboBox {
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.15);
            color: #EAF2FF;
            border-radius: 6px;
            padding: 2px 6px;
        }

        """

def _light_qss() -> str:
        return """
        QWidget { background: #ffffff; color: #111111; font-size: 14px; }
        QLabel { color: #222222; }
        QLineEdit, QTextEdit, QListWidget {
            background: #ffffff; color: #111111; border: 1px solid #cfcfcf; border-radius: 6px; padding: 6px;
        }
        QPushButton {
            background: #f3f3f3; color: #111111; border: 1px solid #cfcfcf; border-radius: 8px; padding: 6px 10px;
        }
        QPushButton:pressed { background: #e0e0e0; }
        QTabWidget::pane { border: 1px solid #cfcfcf; border-radius: 8px; }
        QTabBar::tab {
            background: #f6f6f6; padding: 8px 12px; border: 1px solid #cfcfcf; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px;
        }
        QTabBar::tab:selected { background: #ffffff; }
        QComboBox {
            background: #ffffff; color: #111111; border: 1px solid #cfcfcf; border-radius: 6px; padding: 4px 8px;
        }
        QComboBox QAbstractItemView { background: #ffffff; color: #111111; selection-background-color: #e6f0ff; }
        QProgressBar { border: 1px solid #cfcfcf; border-radius: 6px; height: 16px; text-align: center; }
        """

def _dark_qss() -> str:
        return """
        QWidget { background: #121212; color: #e6e6e6; font-size: 14px; }
        QLabel { color: #e6e6e6; }
        QLineEdit, QTextEdit, QListWidget {
            background: #1e1e1e; color: #e6e6e6; border: 1px solid #3a3a3a; border-radius: 6px; padding: 6px;
        }
        QPushButton {
            background: #232323; color: #e6e6e6; border: 1px solid #3a3a3a; border-radius: 8px; padding: 6px 10px;
        }
        QPushButton:pressed { background: #333333; }
        QTabWidget::pane { border: 1px solid #3a3a3a; border-radius: 8px; }
        QTabBar::tab {
            background: #1a1a1a; padding: 8px 12px; border: 1px solid #3a3a3a; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; color: #cccccc;
        }
        QTabBar::tab:selected { background: #121212; color: #ffffff; }
        QComboBox {
            background: #1e1e1e; color: #e6e6e6; border: 1px solid #3a3a3a; border-radius: 6px; padding: 4px 8px;
        }
        QComboBox QAbstractItemView { background: #1e1e1e; color: #e6e6e6; selection-background-color: #2a3c55; }
        QListWidget::item:selected { background: #2a3c55; }
        QProgressBar { border: 1px solid #3a3a3a; border-radius: 6px; height: 16px; text-align: center; }
        """