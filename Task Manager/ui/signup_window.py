# ui/signup_window.py
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import os

from db.database import add_user


class SignupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sign Up")
        self.setFixedSize(360, 300)

        # ---- Aurora (dark) styling to match Login ----
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                           stop:0 #0f1424, stop:0.5 #151a2d, stop:1 #1b213a);
                color: #EAF2FF; font-family: "Segoe UI"; font-size: 13px;
            }
            QLabel { color: #EAF2FF; font-weight: 600; }

            QLineEdit {
                background: rgba(255,255,255,0.06);
                color: #EAF2FF;
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 10px;
                padding: 8px 10px;
            }
            QLineEdit:focus { border: 1px solid #7AA2F7; }

            /* Primary buttons (match Login) */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 #4A5EEA, stop:1 #6ED3FF);
                color: #ffffff; border: 0; border-radius: 10px; padding: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 #5567f0, stop:1 #7ae0ff);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 #3d54d9, stop:1 #55c7f5);
            }

            /* Small chip-style button for Show/Hide */
            QPushButton#showPwBtn {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.12);
                padding: 8px 10px; min-width: 64px;
            }
            QPushButton#showPwBtn:hover {
                border: 1px solid rgba(122,162,247,0.45);
                background: rgba(122,162,247,0.12);
            }
        """)

        # ---- Banner/logo (same as login) ----
        banner = QLabel()
        banner.setAlignment(Qt.AlignCenter)
        banner_path = os.path.join("assets", "images", "task5_banner.png")
        if not os.path.exists(banner_path):
            fallback = os.path.join("assets", "images", "task5.png")
            banner_path = fallback if os.path.exists(fallback) else None
        if banner_path:
            pm = QPixmap(banner_path)
            if not pm.isNull():
                banner.setPixmap(pm.scaledToWidth(300, Qt.SmoothTransformation))

        # ---- Title ----
        title = QLabel("Create a New Account")

        # ---- Inputs ----
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("New Username")

        pw_row = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("New Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.show_pw_btn = QPushButton("Show")
        self.show_pw_btn.setObjectName("showPwBtn")
        self.show_pw_btn.setCheckable(True)
        self.show_pw_btn.toggled.connect(
            lambda on: self.password_input.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password)
        )
        self.show_pw_btn.toggled.connect(lambda on: self.show_pw_btn.setText("Hide" if on else "Show"))

        pw_row.addWidget(self.password_input, 1)
        pw_row.addWidget(self.show_pw_btn, 0)

        # ---- Actions ----
        self.signup_button = QPushButton("Create Account")
        self.signup_button.clicked.connect(self.signup)

        # Enter submits; Esc closes
        self.username_input.returnPressed.connect(self.signup_button.click)
        self.password_input.returnPressed.connect(self.signup_button.click)
        self.installEventFilter(self)

        # ---- Layout ----
        layout = QVBoxLayout()
        if banner.pixmap():
            layout.addWidget(banner)
        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addLayout(pw_row)
        layout.addSpacing(6)
        layout.addWidget(self.signup_button)
        layout.addStretch(1)
        self.setLayout(layout)

    # Allow Esc to close
    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.close()
            return True
        return super().eventFilter(obj, event)

    def signup(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Both username and password are required.")
            return
        if len(username) < 3:
            QMessageBox.warning(self, "Input Error", "Username must be at least 3 characters long.")
            return
        if len(password) < 4:
            QMessageBox.warning(self, "Input Error", "Password must be at least 4 characters long.")
            return

        success = add_user(username, password)
        if success:
            QMessageBox.information(self, "Success", "Account created. Please log in.")
            self.close()
        else:
            QMessageBox.warning(self, "Signup Failed", "Username already taken.")
