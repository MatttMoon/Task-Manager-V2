# ui/task_widget.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QMessageBox
from db.database import complete_task, delete_task

class TaskWidget(QWidget):
    def __init__(self, task, parent_window):
        super().__init__()
        self.task = task  # (id, user_id, title, description, complete, due_date)
        self.parent_window = parent_window

        self.layout = QHBoxLayout()

        # Add a visual status symbol (✅/❌)
        status = "✅" if task[4] else "❌"
        self.label = QLabel(f"{status} [{task[0]}] {task[2]}")  # e.g. "❌ [3] Wash dishes"

        # Show a button for marking complete only if not already done
        self.complete_btn = QPushButton("✔️ Done" if task[4] else "Mark Done")
        self.delete_btn = QPushButton("Delete")

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.complete_btn)
        self.layout.addWidget(self.delete_btn)
        self.setLayout(self.layout)

        if not task[4]:
            self.complete_btn.clicked.connect(self.mark_done)
        else:
            self.complete_btn.setDisabled(True)

        self.delete_btn.clicked.connect(self.confirm_delete)

    def mark_done(self):
        complete_task(self.task[0], self.task[1])  # task_id, user_id
        self.parent_window.refresh_tasks()

    def confirm_delete(self):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{self.task[2]}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_task(self.task[0])
            self.parent_window.refresh_tasks()
