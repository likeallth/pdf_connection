import sys
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
