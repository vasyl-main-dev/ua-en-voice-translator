import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.core.paths import package_manifest, resource_root
from app.core.runtime import detect_compute_profile
from app.ui.main_window import MainWindow



def run_runtime_check() -> int:
    """Verify the frozen universal build cannot select CUDA."""

    profile = detect_compute_profile()
    return 0 if profile.device == "cpu" else 2


def run_package_check() -> int:
    """Validate metadata embedded in a packaged application."""

    manifest = package_manifest()
    runtime_profile = manifest.get("runtime_profile")
    speech_model = manifest.get("speech_model")
    valid = (
        runtime_profile in {"cpu", "cuda"}
        and speech_model in {"medium", "large-v3"}
    )
    print(
        "Package profile: "
        f"runtime={runtime_profile}, speech_model={speech_model}"
    )
    return 0 if valid else 2


def main() -> int:
    if "--runtime-check" in sys.argv:
        return run_runtime_check()
    if "--package-check" in sys.argv:
        return run_package_check()

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

    return application.exec()


if __name__ == "__main__":
    sys.exit(main())
