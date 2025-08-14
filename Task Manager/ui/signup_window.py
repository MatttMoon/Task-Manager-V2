# ui/signup_window.py
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox
)
from db.database import add_user

class SignupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sign Up")
        self.setFixedSize(300, 200)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("New Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("New Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.signup_button = QPushButton("Create Account")
        self.signup_button.clicked.connect(self.signup)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Create a New Account"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.signup_button)

        self.setLayout(layout)

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
