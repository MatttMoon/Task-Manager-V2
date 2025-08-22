import sys
import os

# High-DPI fixes (safe defaults)
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from ui.login_window import LoginWindow
from db.database import init_db


def resource_path(*parts):
    """
    Return absolute path to a bundled resource.
    Works in dev and in PyInstaller (--onefile) builds.
    """
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, *parts)


if __name__ == "__main__":
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("Task5")
    app.setOrganizationName("Task5") 

    # === Set application icon ===
    app_icon_path = resource_path("assets", "icons", "task5.ico")
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))

    wnd = LoginWindow()
    wnd.setWindowTitle("Task5 - Login") 
    wnd.show()

    sys.exit(app.exec_())
