from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)
from ui.main_window import MainWindow
from ui.signup_window import SignupWindow
from db.database import validate_user
from PyQt5.QtGui import QFont

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        self.setWindowTitle("Login")
        self.setFixedSize(300, 200)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)

        self.signup_button = QPushButton("Sign Up")
        self.signup_button.clicked.connect(self.open_signup)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Login to Task Manager"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.signup_button)

        self.setLayout(layout)

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
