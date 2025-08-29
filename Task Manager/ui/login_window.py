from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
import os
import sys

from ui.main_window import MainWindow
from ui.signup_window import SignupWindow
from db.database import validate_user


def resource_path(*parts):
    """
    Return absolute path to a bundled resource.
    Works in dev and in PyInstaller (--onefile) builds.
    """
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, *parts)


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        # --- Window basics ---
        self.setWindowTitle("Login")
        self.setFixedSize(340, 420)
        font = QFont("Segoe UI", 10)
        self.setFont(font)

        # --- Aurora ---
        self.setStyleSheet("""
        QWidget { background: #0f1424; color: #EAF2FF; }
        QLabel { color: #EAF2FF; }
        QLineEdit {
            background: #1b213a;
            color: #EAF2FF;
            border: 1px solid #2c3352;
            border-radius: 8px;
            padding: 8px 10px;
        }
        QLineEdit:focus { border-color: #7AA2F7; }
        QPushButton {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #4A5EEA, stop:1 #6ED3FF);
            color: #ffffff;
            border: 0; border-radius: 10px; padding: 8px 12px;
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #3d54d9, stop:1 #55c7f5);
        }
        """)

        # --- Banner/logo ---
        banner_label = QLabel(alignment=Qt.AlignCenter)
        banner_path = resource_path("assets", "images", "task5_banner.png")
        if os.path.exists(banner_path):
            pixmap = QPixmap(banner_path).scaledToWidth(280, Qt.SmoothTransformation)
            banner_label.setPixmap(pixmap)
        else:
            banner_label.setText("Task5")
            banner_label.setStyleSheet("font-size: 22px; font-weight: 600;")

        # --- Inputs ---
        self.username_input = QLineEdit(placeholderText="Username")
        self.password_input = QLineEdit(placeholderText="Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Press Enter to login
        self.username_input.returnPressed.connect(self._focus_password)
        self.password_input.returnPressed.connect(self.login)

        # --- Buttons ---
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)

        self.signup_button = QPushButton("Sign Up")
        self.signup_button.clicked.connect(self.open_signup)
        
        # --- Layout ---
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        # Center stack with some top/bottom air
        root.addSpacerItem(QSpacerItem(0, 6, QSizePolicy.Minimum, QSizePolicy.Fixed))
        root.addWidget(banner_label)

        title = QLabel("Login to Task5")
        title.setStyleSheet("color:#DDE9FF; font-size: 14px; margin-top: 4px;")
        title.setAlignment(Qt.AlignLeft)
        root.addWidget(title)

        root.addWidget(self.username_input)
        root.addWidget(self.password_input)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.login_button)
        btn_row.addWidget(self.signup_button)
        root.addLayout(btn_row)

        root.addStretch(1)

    # -------------------- Actions --------------------
    def _focus_password(self):
        self.password_input.setFocus(Qt.TabFocusReason)

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter both username and password.")
            return

        user = validate_user(username, password)
        if user:
            self.main_window = MainWindow(user)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

    def open_signup(self):
        self.signup_window = SignupWindow()
        self.signup_window.show()
