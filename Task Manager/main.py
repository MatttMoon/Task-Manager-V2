import sys
import os
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

from PyQt5.QtWidgets import QApplication
from ui import login_window
from ui.login_window import LoginWindow
from db.database import init_db

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
