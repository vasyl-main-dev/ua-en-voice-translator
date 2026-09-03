from pathlib import Path
from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from app.services.translator import Translator
from app.services.audio_recorder import AudioRecorder
from app.services.speech_recognizer import SpeechRecognizer
from app.workers.translation_worker import TranslationWorker
from app.workers.voice_processing_worker import VoiceProcessingWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.source_language = "uk"
        self.target_language = "en"

        self.translator = Translator()

        self.audio_recorder = AudioRecorder()

        self.speech_recognizer = SpeechRecognizer(
            model_size="small",
            device="cuda",
            compute_type="float16",
        )

        project_root = Path(__file__).resolve().parents[2]
        self.recording_path = (
                project_root / "recordings" / "latest_recording.wav"
        )

        self.translation_thread: QThread | None = None
        self.translation_worker: TranslationWorker | None = None

        self.voice_thread: QThread | None = None
        self.voice_worker: VoiceProcessingWorker | None = None

        self.setWindowTitle("UA ↔ EN Voice Translator")
        self.resize(1000, 650)

        self.create_interface()

    def create_interface(self) -> None:
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        language_layout = self.create_language_layout()
        text_layout = self.create_text_layout()
        button_layout = self.create_button_layout()

        main_layout.addLayout(language_layout)
        main_layout.addLayout(text_layout)
        main_layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)
        self.statusBar().showMessage("Програма готова до роботи")

    def create_language_layout(self) -> QHBoxLayout:
        language_layout = QHBoxLayout()

        self.source_language_label = QLabel("Українська")
        self.source_language_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.swap_button = QPushButton("⇄")
        self.swap_button.setToolTip("Змінити напрямок перекладу")
        self.swap_button.setFixedWidth(60)
        self.swap_button.clicked.connect(self.swap_languages)

        self.target_language_label = QLabel("English")
        self.target_language_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        language_layout.addWidget(self.source_language_label)
        language_layout.addWidget(self.swap_button)
        language_layout.addWidget(self.target_language_label)

        return language_layout

    def create_text_layout(self) -> QHBoxLayout:
        text_layout = QHBoxLayout()
        text_layout.setSpacing(15)

        source_layout = QVBoxLayout()
        source_title = QLabel("Розпізнаний або введений текст")

        self.source_text_edit = QTextEdit()
        self.source_text_edit.setPlaceholderText(
            "Введіть український текст або скористайтеся мікрофоном..."
        )

        source_layout.addWidget(source_title)
        source_layout.addWidget(self.source_text_edit)

        translation_layout = QVBoxLayout()
        translation_title = QLabel("Переклад")

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

        self.record_button = QPushButton("🎤 Записати")
        self.record_button.clicked.connect(self.handle_record)

        self.translate_button = QPushButton("Перекласти")
        self.translate_button.clicked.connect(self.handle_translate)

        self.copy_button = QPushButton("Копіювати переклад")
        self.copy_button.clicked.connect(self.copy_translation)

        self.clear_button = QPushButton("Очистити")
        self.clear_button.clicked.connect(self.clear_text)

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
                "Введіть український текст або скористайтеся мікрофоном..."
            )
            self.translation_text_edit.setPlaceholderText(
                "Тут з’явиться переклад англійською..."
            )
        else:
            self.source_language_label.setText("English")
            self.target_language_label.setText("Українська")

            self.source_text_edit.setPlaceholderText(
                "Enter English text or use the microphone..."
            )
            self.translation_text_edit.setPlaceholderText(
                "Тут з’явиться переклад українською..."
            )

        self.statusBar().showMessage(
            f"Напрямок: {self.source_language} → {self.target_language}"
        )

    def handle_record(self) -> None:
        if self.audio_recorder.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        if self.voice_thread is not None:
            self.statusBar().showMessage(
                "Попередній запис ще обробляється"
            )
            return

        try:
            self.audio_recorder.start()
        except Exception as error:
            QMessageBox.critical(
                self,
                "Помилка запису",
                str(error),
            )
            return

        self.source_text_edit.clear()
        self.translation_text_edit.clear()

        self.set_recording_running(True)
        self.statusBar().showMessage(
            "Записування... Натисніть кнопку ще раз для завершення"
        )

    def stop_recording(self) -> None:
        try:
            audio_path = self.audio_recorder.stop(
                self.recording_path
            )
        except Exception as error:
            self.set_recording_running(False)

            QMessageBox.critical(
                self,
                "Помилка запису",
                str(error),
            )
            return

        self.set_recording_running(False)
        self.start_voice_processing(audio_path)

    def set_recording_running(self, is_recording: bool) -> None:
        self.swap_button.setDisabled(is_recording)
        self.translate_button.setDisabled(is_recording)
        self.copy_button.setDisabled(is_recording)
        self.clear_button.setDisabled(is_recording)

        if is_recording:
            self.record_button.setText("⏹ Зупинити")
        else:
            self.record_button.setText("🎤 Записати")

    def start_voice_processing(
            self,
            audio_path: Path,
    ) -> None:
        if self.voice_thread is not None:
            return

        self.set_voice_processing_running(True)
        self.statusBar().showMessage(
            "Підготовка до розпізнавання..."
        )

        self.voice_thread = QThread(self)

        self.voice_worker = VoiceProcessingWorker(
            audio_path=audio_path,
            speech_recognizer=self.speech_recognizer,
            translator=self.translator,
            source_language=self.source_language,
            target_language=self.target_language,
        )

        self.voice_worker.moveToThread(self.voice_thread)

        self.voice_thread.started.connect(
            self.voice_worker.run
        )

        self.voice_worker.stage_changed.connect(
            self.statusBar().showMessage
        )
        self.voice_worker.recognized.connect(
            self.source_text_edit.setPlainText
        )
        self.voice_worker.translated.connect(
            self.handle_voice_translation_finished
        )
        self.voice_worker.failed.connect(
            self.handle_voice_processing_failed
        )

        self.voice_worker.finished.connect(
            self.voice_thread.quit
        )
        self.voice_worker.finished.connect(
            self.voice_worker.deleteLater
        )

        self.voice_thread.finished.connect(
            self.cleanup_voice_thread
        )
        self.voice_thread.finished.connect(
            self.voice_thread.deleteLater
        )

        self.voice_thread.start()

        def handle_voice_translation_finished(
                self,
                translated_text: str,
        ) -> None:
            self.translation_text_edit.setPlainText(
                translated_text
            )
            self.statusBar().showMessage(
                "Голосовий переклад завершено"
            )

        def handle_voice_processing_failed(
                self,
                error_message: str,
        ) -> None:
            self.statusBar().showMessage(
                "Помилка голосової обробки"
            )

            QMessageBox.critical(
                self,
                "Помилка голосового перекладу",
                error_message,
            )

        def cleanup_voice_thread(self) -> None:
            self.voice_worker = None
            self.voice_thread = None

            self.set_voice_processing_running(False)

        def set_voice_processing_running(
                self,
                is_running: bool,
        ) -> None:
            self.record_button.setDisabled(is_running)
            self.translate_button.setDisabled(is_running)
            self.swap_button.setDisabled(is_running)
            self.copy_button.setDisabled(is_running)
            self.clear_button.setDisabled(is_running)

            if is_running:
                self.record_button.setText("Обробка...")
            else:
                self.record_button.setText("🎤 Записати")

    def handle_voice_translation_finished(
            self,
            translated_text: str,
    ) -> None:
        self.translation_text_edit.setPlainText(
            translated_text
        )
        self.statusBar().showMessage(
            "Голосовий переклад завершено"
        )

    def handle_voice_processing_failed(
            self,
            error_message: str,
    ) -> None:
        self.statusBar().showMessage(
            "Помилка голосової обробки"
        )

        QMessageBox.critical(
            self,
            "Помилка голосового перекладу",
            error_message,
        )

    def cleanup_voice_thread(self) -> None:
        self.voice_worker = None
        self.voice_thread = None

        self.set_voice_processing_running(False)

    def set_voice_processing_running(
            self,
            is_running: bool,
    ) -> None:
        self.record_button.setDisabled(is_running)
        self.translate_button.setDisabled(is_running)
        self.swap_button.setDisabled(is_running)
        self.copy_button.setDisabled(is_running)
        self.clear_button.setDisabled(is_running)

        if is_running:
            self.record_button.setText("Обробка...")
        else:
            self.record_button.setText("🎤 Записати")

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

        self.translation_thread.started.connect(
            self.translation_worker.run
        )

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

    def handle_translation_finished(
            self,
            translated_text: str,
    ) -> None:
        self.translation_text_edit.setPlainText(translated_text)
        self.statusBar().showMessage("Переклад завершено")
        self.set_translation_running(False)

    def handle_translation_failed(
            self,
            error_message: str,
    ) -> None:
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

        if is_running:
            self.translate_button.setText("Перекладаємо...")
        else:
            self.translate_button.setText("Перекласти")
