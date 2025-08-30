# core/theme.py
from PyQt5.QtWidgets import QApplication, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor

# ---------------- Public helpers ----------------

def apply_theme_to_app(theme: str, accent: str = "#7AA2F7"):
    """
    Apply one of: 'aurora', 'dark', 'light' to the whole app.
    Accent is used for focus, selections, and subtle cues.
    """
    app = QApplication.instance()
    if not app:
        return
    t = (theme or "aurora").lower()
    if t == "aurora":
        app.setStyleSheet(_aurora_qss(accent))
    elif t == "dark":
        app.setStyleSheet(_dark_qss(accent))
    else:
        app.setStyleSheet(_light_qss(accent))

def apply_accent_to_window(window, hex_color: str):
    """
    Layer widget-scoped accent rules WITHOUT clobbering the app stylesheet.
    """
    accent = hex_color or "#7AA2F7"
    existing = window.styleSheet() or ""
    window.setStyleSheet(existing + f"""
    /* --- Accent (scoped to this window only) --- */
    QLineEdit:focus, QTextEdit:focus, QListWidget:focus, QComboBox:focus {{ border: 1px solid {accent}; }}
    QListWidget::item:selected {{ background: {accent}; color: white; }}
    QPushButton:hover {{ border: 1px solid {accent}; }}
    QProgressBar::chunk {{ background-color: {accent}; }}
    """)

def apply_aurora_effects_if_needed(window, cfg: dict):
    if (cfg or {}).get("theme", "aurora").lower() != "aurora":
        return
    _apply_aurora_effects(window)

def _apply_aurora_effects(window):
    def glow(w, radius=24, alpha=0.22):
        eff = QGraphicsDropShadowEffect(window)
        eff.setColor(QColor(122, 162, 247, int(alpha * 255)))
        eff.setBlurRadius(radius)
        eff.setOffset(0, 6)
        w.setGraphicsEffect(eff)

    for name in ["task_list", "task_details", "search_input", "due_date_input", "level_bar", "calendar", "cal_tasks_list"]:
        w = getattr(window, name, None)
        if w:
            glow(w)

# ---------------- QSS THEMES ----------------

def _calendar_white_qss(accent: str) -> str:
    """Unified white calendar for ALL themes."""
    return f"""
    /* ===== Calendar (Unified White) ===== */
    QCalendarWidget QTableView QHeaderView::section {{
        background: #F3F5FA;
        color: #1A1F2B;
        border: none;
        padding: 6px 0;
    }}
    QCalendarWidget QTableView {{
        background: #FFFFFF;
        color: #111111;
        gridline-color: #E1E5EE;
        outline: 0;
    }}
    QCalendarWidget QTableView::item {{
        background: transparent;
        padding: 6px;
    }}
    QCalendarWidget QTableView::item:selected {{
        background: #E6F0FF;
        border-radius: 6px;
    }}
    QCalendarWidget QWidget#qt_calendar_today {{
        border: 1px solid {accent};
        border-radius: 4px;
    }}
    QCalendarWidget QWidget#qt_calendar_navigationbar {{ background: transparent; }}
    QCalendarWidget QToolButton {{
        background: #F6F7FB;
        border: 1px solid #DFE3EE;
        border-radius: 6px;
        padding: 4px 8px;
        color: #1A1F2B;
    }}
    QCalendarWidget QToolButton:hover {{ background: #EEF2FB; }}
    """

def _aurora_qss(accent: str) -> str:
    return f"""
    /* ===== Base ===== */
    QWidget {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f1424, stop:0.5 #151a2d, stop:1 #1b213a);
        color: #EAF2FF; font-size: 14px;
    }}
    QLabel {{ color: #EAF2FF; }}

    QLineEdit, QTextEdit, QListWidget, QComboBox, QCalendarWidget,
    QTabWidget::pane, QProgressBar {{
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 12px;
        padding: 6px;
    }}
    QLineEdit:focus, QTextEdit:focus, QListWidget:focus, QComboBox:focus {{
        border: 1px solid {accent};
    }}

    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4A5EEA, stop:1 #6ED3FF);
        color: #ffffff; border: 0; border-radius: 10px; padding: 7px 12px;
    }}
    QPushButton[flat="true"] {{
        background: rgba(255,255,255,0.08); color: #EAF2FF;
        border: 1px solid rgba(255,255,255,0.12);
    }}
    QPushButton[flat="true"]:hover {{
        border: 1px solid {accent}66;
        background: {accent}20;
    }}

    QTabBar::tab {{
        background: rgba(255,255,255,0.08);
        color: #DDE9FF; padding: 8px 14px;
        border: 1px solid rgba(255,255,255,0.12);
        border-top-left-radius: 10px; border-top-right-radius: 10px;
        margin-right: 6px;
    }}
    QTabBar::tab:selected {{
        background: {accent}2E; color: #FFFFFF;
        border: 1px solid {accent}59;
    }}

    QListWidget::item {{ padding: 6px; margin: 3px 4px; border-radius: 8px; }}
    QListWidget::item:selected {{ background: {accent}59; color: #FFFFFF; }}

    QComboBox QAbstractItemView {{
        background: rgba(20,25,45,0.98);
        color: #EAF2FF; border: 1px solid rgba(255,255,255,0.12);
        selection-background-color: {accent}59;
    }}

    QProgressBar {{ text-align: center; height: 18px; }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #8A7DFF, stop:1 #4AD0FF);
        border-radius: 8px;
    }}

    { _calendar_white_qss(accent) }
    """

def _light_qss(accent: str) -> str:
    return f"""
    /* ===== Base ===== */
    QWidget {{ background: #ffffff; color: #111111; font-size: 14px; }}
    QLabel {{ color: #222222; }}
    QLineEdit, QTextEdit, QListWidget, QComboBox, QCalendarWidget,
    QTabWidget::pane, QProgressBar {{
        background: #ffffff; color: #111111; border: 1px solid #cfcfcf; border-radius: 6px; padding: 6px;
    }}
    QLineEdit:focus, QTextEdit:focus, QListWidget:focus, QComboBox:focus {{
        border: 1px solid {accent};
    }}
    QPushButton {{
        background: #f3f3f3; color: #111111; border: 1px solid #cfcfcf; border-radius: 8px; padding: 6px 10px;
    }}
    QPushButton:pressed {{ background: #e0e0e0; }}
    QTabWidget::pane {{ border: 1px solid #cfcfcf; border-radius: 8px; }}
    QTabBar::tab {{
        background: #f6f6f6; padding: 8px 12px; border: 1px solid #cfcfcf; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px;
    }}
    QTabBar::tab:selected {{ background: #ffffff; }}

    QComboBox QAbstractItemView {{ background: #ffffff; color: #111111; selection-background-color: {accent}2E; }}
    QListWidget::item:selected {{ background: {accent}59; color: #ffffff; }}
    QProgressBar {{ border: 1px solid #cfcfcf; border-radius: 6px; height: 16px; text-align: center; }}

    { _calendar_white_qss(accent) }
    """

def _dark_qss(accent: str) -> str:
    return f"""
    /* ===== Base ===== */
    QWidget {{ background: #121212; color: #e6e6e6; font-size: 14px; }}
    QLabel {{ color: #e6e6e6; }}
    QLineEdit, QTextEdit, QListWidget, QComboBox, QCalendarWidget,
    QTabWidget::pane, QProgressBar {{
        background: #1e1e1e; color: #e6e6e6; border: 1px solid #3a3a3a; border-radius: 6px; padding: 6px;
    }}
    QLineEdit:focus, QTextEdit:focus, QListWidget:focus, QComboBox:focus {{
        border: 1px solid {accent};
    }}
    QPushButton {{
        background: #232323; color: #e6e6e6; border: 1px solid #3a3a3a; border-radius: 8px; padding: 6px 10px;
    }}
    QPushButton:pressed {{ background: #333333; }}
    QTabWidget::pane {{ border: 1px solid #3a3a3a; border-radius: 8px; }}
    QTabBar::tab {{
        background: #1a1a1a; padding: 8px 12px; border: 1px solid #3a3a3a; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; color: #cccccc;
    }}
    QTabBar::tab:selected {{ background: #121212; color: #ffffff; }}
    QComboBox QAbstractItemView {{ background: #1e1e1e; color: #e6e6e6; selection-background-color: #2a3c55; }}
    QListWidget::item:selected {{ background: #2a3c55; }}

    QProgressBar {{ border: 1px solid #3a3a3a; border-radius: 6px; height: 16px; text-align: center; }}

    { _calendar_white_qss(accent) }
    """

# ---------------- Convenience ----------------

def reapply_theme(window, theme: str, accent: str = "#7AA2F7"):
    """
    Call this after toggling theme in your settings UI.
    Also refreshes the calendar painting if present.
    """
    apply_theme_to_app(theme, accent)
    if hasattr(window, "cfg"):
        window.cfg["theme"] = theme
        window.cfg["accent"] = accent
    if hasattr(window, "calendar"):
        try:
            from ui.calendar_tab import refresh_calendar_marks as _refresh
            _refresh(window)
        except Exception:
            pass
