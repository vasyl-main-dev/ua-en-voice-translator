from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from app.services.speech_recognizer import SpeechRecognizer
from app.services.translator import Translator


class VoiceProcessingWorker(QObject):
    recognized = Signal(str)
    translated = Signal(str)
    stage_changed = Signal(str)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        audio_path: Path,
        speech_recognizer: SpeechRecognizer,
        translator: Translator,
        source_language: str,
        target_language: str,
    ) -> None:
        super().__init__()

        self.audio_path = audio_path
        self.speech_recognizer = speech_recognizer
        self.translator = translator
        self.source_language = source_language
        self.target_language = target_language

    @Slot()
    def run(self) -> None:
        try:
            self.stage_changed.emit("Розпізнавання мовлення...")

            recognized_text = self.speech_recognizer.transcribe(
                audio_path=self.audio_path,
                language=self.source_language,
            )

            if not recognized_text:
                raise RuntimeError(
                    "Whisper не зміг розпізнати мовлення"
                )

            self.recognized.emit(recognized_text)

            self.stage_changed.emit("Переклад тексту...")

            translated_text = self.translator.translate(
                text=recognized_text,
                source_language=self.source_language,
                target_language=self.target_language,
            )

            self.translated.emit(translated_text)

        except Exception as error:
            self.failed.emit(str(error))

        finally:
            self.finished.emit()
