import sys
import os

# Set Qt platform plugin path explicitly for PyInstaller frozen app
if getattr(sys, 'frozen', False):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(sys._MEIPASS, "PyQt6", "Qt6", "plugins", "platforms")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from gui import MainWindow

def main():
    # Support High DPI scaling on Windows
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
