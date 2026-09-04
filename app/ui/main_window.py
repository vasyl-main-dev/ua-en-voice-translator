from __future__ import annotations

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QCloseEvent, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.speech_recognizer import SpeechRecognizer
from app.services.translator import Translator
from app.workers.continuous_translation_worker import (
    ContinuousTranslationWorker,
)
from app.workers.translation_worker import TranslationWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.source_language = "uk"
        self.target_language = "en"

        self.translator = Translator()
        self.speech_recognizer = SpeechRecognizer(model_size="small")

        self.translation_thread: QThread | None = None
        self.translation_worker: TranslationWorker | None = None

        self.continuous_thread: QThread | None = None
        self.continuous_worker: ContinuousTranslationWorker | None = None
        self.continuous_seconds = 0
        self.closing_after_stop = False

        self.continuous_timer = QTimer(self)
        self.continuous_timer.setInterval(1_000)
        self.continuous_timer.timeout.connect(
            self.update_continuous_duration
        )

        self.setWindowTitle("UA ↔ EN Voice Translator")
        self.resize(1_000, 650)
        self.create_interface()

    def create_interface(self) -> None:
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        main_layout.addLayout(self.create_language_layout())
        main_layout.addLayout(self.create_text_layout())
        main_layout.addLayout(self.create_button_layout())

        self.runtime_label = QLabel(
            f"Обчислення: {self.speech_recognizer.runtime_description}"
        )
        self.runtime_label.setObjectName("runtimeLabel")
        main_layout.addWidget(self.runtime_label)

        self.setCentralWidget(central_widget)
        self.statusBar().showMessage("Програма готова до роботи")

    def create_language_layout(self) -> QHBoxLayout:
        language_layout = QHBoxLayout()

        self.source_language_label = QLabel("Українська")
        self.source_language_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.source_language_label.setObjectName("languageLabel")

        self.swap_button = QPushButton("⇄")
        self.swap_button.setToolTip("Змінити напрямок перекладу")
        self.swap_button.setFixedWidth(60)
        self.swap_button.clicked.connect(self.swap_languages)
        self.swap_button.setObjectName("swapButton")

        self.target_language_label = QLabel("English")
        self.target_language_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.target_language_label.setObjectName("languageLabel")

        language_layout.addWidget(self.source_language_label)
        language_layout.addWidget(self.swap_button)
        language_layout.addWidget(self.target_language_label)
        return language_layout

    def create_text_layout(self) -> QHBoxLayout:
        text_layout = QHBoxLayout()
        text_layout.setSpacing(15)

        source_layout = QVBoxLayout()
        source_title = QLabel("Розпізнаний або введений текст")
        source_title.setObjectName("panelTitle")
        self.source_text_edit = QTextEdit()
        self.source_text_edit.setPlaceholderText(
            "Введіть український текст або почніть голосовий переклад..."
        )
        source_layout.addWidget(source_title)
        source_layout.addWidget(self.source_text_edit)

        translation_layout = QVBoxLayout()
        translation_title = QLabel("Переклад")
        translation_title.setObjectName("panelTitle")
        self.translation_text_edit = QTextEdit()
        self.translation_text_edit.setPlaceholderText(
            "Тут з’явиться переклад англійською..."
        )
        self.translation_text_edit.setReadOnly(True)
        translation_layout.addWidget(translation_title)
        translation_layout.addWidget(self.translation_text_edit)

        text_layout.addLayout(source_layout)
        text_layout.addLayout(translation_layout)
        return text_layout

    def create_button_layout(self) -> QHBoxLayout:
        button_layout = QHBoxLayout()

        self.record_button = QPushButton("🎤 Почати переклад")
        self.record_button.clicked.connect(self.handle_continuous_translation)
        self.record_button.setObjectName("recordButton")
        self.record_button.setProperty("recording", False)

        self.translate_button = QPushButton("Перекласти текст")
        self.translate_button.clicked.connect(self.handle_translate)
        self.translate_button.setObjectName("translateButton")

        self.copy_button = QPushButton("Копіювати переклад")
        self.copy_button.clicked.connect(self.copy_translation)
        self.copy_button.setObjectName("copyButton")

        self.clear_button = QPushButton("Очистити")
        self.clear_button.clicked.connect(self.clear_text)
        self.clear_button.setObjectName("clearButton")

        button_layout.addWidget(self.record_button)
        button_layout.addStretch()
        button_layout.addWidget(self.translate_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.clear_button)
        return button_layout

    def swap_languages(self) -> None:
        self.source_language, self.target_language = (
            self.target_language,
            self.source_language,
        )

        if self.source_language == "uk":
            self.source_language_label.setText("Українська")
            self.target_language_label.setText("English")
            self.source_text_edit.setPlaceholderText(
                "Введіть український текст або почніть голосовий переклад..."
            )
            self.translation_text_edit.setPlaceholderText(
                "Тут з’явиться переклад англійською..."
            )
        else:
            self.source_language_label.setText("English")
            self.target_language_label.setText("Українська")
            self.source_text_edit.setPlaceholderText(
                "Enter English text or start voice translation..."
            )
            self.translation_text_edit.setPlaceholderText(
                "Тут з’явиться переклад українською..."
            )

        self.statusBar().showMessage(
            f"Напрямок: {self.source_language} → {self.target_language}"
        )

    def handle_continuous_translation(self) -> None:
        if self.continuous_thread is None:
            self.start_continuous_translation()
        else:
            self.stop_continuous_translation()

    def start_continuous_translation(self) -> None:
        if self.translation_thread is not None:
            self.statusBar().showMessage(
                "Дочекайтеся завершення текстового перекладу"
            )
            return

        self.source_text_edit.clear()
        self.translation_text_edit.clear()
        self.continuous_seconds = 0
        self.set_continuous_running(True)
        self.record_button.setText("Запуск мікрофона...")
        self.record_button.setDisabled(True)
        self.statusBar().showMessage("Запускаємо мікрофон...")

        self.continuous_thread = QThread(self)
        self.continuous_worker = ContinuousTranslationWorker(
            speech_recognizer=self.speech_recognizer,
            translator=self.translator,
            source_language=self.source_language,
            target_language=self.target_language,
        )
        self.continuous_worker.moveToThread(self.continuous_thread)

        self.continuous_thread.started.connect(
            self.continuous_worker.run
        )
        self.continuous_worker.recording_started.connect(
            self.handle_continuous_started
        )
        self.continuous_worker.stage_changed.connect(
            self.statusBar().showMessage
        )
        self.continuous_worker.recognized.connect(
            self.append_recognized_text
        )
        self.continuous_worker.translated.connect(
            self.append_translated_text
        )
        self.continuous_worker.failed.connect(
            self.handle_continuous_failed
        )
        self.continuous_worker.finished.connect(
            self.continuous_thread.quit
        )
        self.continuous_worker.finished.connect(
            self.continuous_worker.deleteLater
        )
        self.continuous_thread.finished.connect(
            self.cleanup_continuous_thread
        )
        self.continuous_thread.finished.connect(
            self.continuous_thread.deleteLater
        )
        self.continuous_thread.start()

    def handle_continuous_started(self) -> None:
        self.record_button.setDisabled(False)
        self.update_continuous_duration()
        self.continuous_timer.start()

    def stop_continuous_translation(self) -> None:
        if self.continuous_worker is None:
            return

        self.continuous_timer.stop()
        self.record_button.setDisabled(True)
        self.record_button.setText("Завершення...")
        self.statusBar().showMessage(
            "Зупиняємо запис і завершуємо обробку аудіо..."
        )
        self.continuous_worker.request_stop()

    def append_recognized_text(self, text: str) -> None:
        self._append_paragraph(self.source_text_edit, text)
        self.refresh_runtime_label()

    def append_translated_text(self, text: str) -> None:
        self._append_paragraph(self.translation_text_edit, text)

    @staticmethod
    def _append_paragraph(text_edit: QTextEdit, text: str) -> None:
        cursor = text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if text_edit.toPlainText():
            cursor.insertBlock()

        cursor.insertText(text)
        text_edit.setTextCursor(cursor)
        text_edit.ensureCursorVisible()

    def handle_continuous_failed(self, error_message: str) -> None:
        self.statusBar().showMessage("Помилка безперервного перекладу")
        QMessageBox.critical(
            self,
            "Помилка голосового перекладу",
            error_message,
        )

    def cleanup_continuous_thread(self) -> None:
        self.continuous_worker = None
        self.continuous_thread = None
        self.continuous_timer.stop()
        self.set_continuous_running(False)
        self.refresh_runtime_label()

        if self.closing_after_stop:
            self.closing_after_stop = False
            self.close()
        else:
            self.statusBar().showMessage("Голосовий переклад завершено")

    def set_continuous_running(self, is_running: bool) -> None:
        self.swap_button.setDisabled(is_running)
        self.translate_button.setDisabled(is_running)
        self.clear_button.setDisabled(is_running)
        self.source_text_edit.setReadOnly(is_running)

        self.record_button.setProperty("recording", is_running)
        self.record_button.style().unpolish(self.record_button)
        self.record_button.style().polish(self.record_button)
        self.record_button.update()

        if is_running:
            self.record_button.setText("⏹ Зупинити 00:00")
        else:
            self.record_button.setDisabled(False)
            self.record_button.setText("🎤 Почати переклад")

    def update_continuous_duration(self) -> None:
        minutes, seconds = divmod(self.continuous_seconds, 60)
        self.record_button.setText(
            f"⏹ Зупинити {minutes:02d}:{seconds:02d}"
        )
        self.continuous_seconds += 1

    def refresh_runtime_label(self) -> None:
        self.runtime_label.setText(
            f"Обчислення: {self.speech_recognizer.runtime_description}"
        )

    def handle_translate(self) -> None:
        source_text = self.source_text_edit.toPlainText().strip()

        if not source_text:
            self.statusBar().showMessage("Спочатку введіть текст")
            return

        if self.translation_thread is not None:
            self.statusBar().showMessage("Переклад уже виконується")
            return

        self.set_translation_running(True)
        self.statusBar().showMessage("Виконується переклад...")
        self.translation_thread = QThread(self)
        self.translation_worker = TranslationWorker(
            translator=self.translator,
            text=source_text,
            source_language=self.source_language,
            target_language=self.target_language,
        )
        self.translation_worker.moveToThread(self.translation_thread)

        self.translation_thread.started.connect(self.translation_worker.run)
        self.translation_worker.translation_finished.connect(
            self.handle_translation_finished
        )
        self.translation_worker.translation_failed.connect(
            self.handle_translation_failed
        )
        self.translation_worker.finished.connect(
            self.translation_thread.quit
        )
        self.translation_worker.finished.connect(
            self.translation_worker.deleteLater
        )
        self.translation_thread.finished.connect(
            self.cleanup_translation_thread
        )
        self.translation_thread.finished.connect(
            self.translation_thread.deleteLater
        )
        self.translation_thread.start()

    def handle_translation_finished(self, translated_text: str) -> None:
        self.translation_text_edit.setPlainText(translated_text)
        self.statusBar().showMessage("Переклад завершено")
        self.set_translation_running(False)

    def handle_translation_failed(self, error_message: str) -> None:
        self.statusBar().showMessage("Помилка перекладу")
        self.set_translation_running(False)
        QMessageBox.critical(
            self,
            "Помилка перекладу",
            error_message,
        )

    def cleanup_translation_thread(self) -> None:
        self.translation_worker = None
        self.translation_thread = None

    def set_translation_running(self, is_running: bool) -> None:
        self.translate_button.setDisabled(is_running)
        self.swap_button.setDisabled(is_running)
        self.record_button.setDisabled(is_running)
        self.copy_button.setDisabled(is_running)
        self.clear_button.setDisabled(is_running)
        self.translate_button.setText(
            "Перекладаємо..." if is_running else "Перекласти текст"
        )

    def copy_translation(self) -> None:
        translation = self.translation_text_edit.toPlainText()
        if not translation:
            self.statusBar().showMessage("Немає перекладу для копіювання")
            return

        QApplication.clipboard().setText(translation)
        self.statusBar().showMessage("Переклад скопійовано")

    def clear_text(self) -> None:
        self.source_text_edit.clear()
        self.translation_text_edit.clear()
        self.statusBar().showMessage("Текст очищено")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.continuous_thread is not None:
            self.closing_after_stop = True
            self.stop_continuous_translation()
            event.ignore()
            return

        if self.translation_thread is not None:
            QMessageBox.information(
                self,
                "Обробка ще триває",
                "Дочекайтеся завершення перекладу.",
            )
            event.ignore()
            return

        event.accept()
