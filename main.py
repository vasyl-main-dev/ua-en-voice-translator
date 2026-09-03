import sys


from PySide6.QtWidgets import QApplication
from pathlib import Path

from app.ui.main_window import MainWindow



def main() -> None:
    application = QApplication(sys.argv)
    stylesheet_path = (
            Path(__file__).resolve().parent
            / "app"
            / "ui"
            / "styles.qss"
    )

    if stylesheet_path.exists():
        stylesheet = stylesheet_path.read_text(
            encoding="utf-8"
        )
        application.setStyleSheet(stylesheet)

    window = MainWindow()
    window.show()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()
