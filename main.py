import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.core.paths import resource_root
from app.ui.main_window import MainWindow



def main() -> None:
    application = QApplication(sys.argv)
    stylesheet_path = resource_root() / "app" / "ui" / "styles.qss"

    if stylesheet_path.exists():
        stylesheet = stylesheet_path.read_text(
            encoding="utf-8"
        )
        application.setStyleSheet(stylesheet)

    try:
        window = MainWindow()
    except Exception as error:
        QMessageBox.critical(
            None,
            "Помилка запуску",
            "Не вдалося запустити програму:\n\n"
            f"{error}",
        )
        raise
    window.show()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()
