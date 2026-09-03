from PySide6.QtCore import QObject, Signal, Slot

from app.services.translator import Translator


class TranslationWorker(QObject):
    translation_finished = Signal(str)
    translation_failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        translator: Translator,
        text: str,
        source_language: str,
        target_language: str,
    ) -> None:
        super().__init__()

        self.translator = translator
        self.text = text
        self.source_language = source_language
        self.target_language = target_language

    @Slot()
    def run(self) -> None:
        try:
            translated_text = self.translator.translate(
                text=self.text,
                source_language=self.source_language,
                target_language=self.target_language,
            )
        except Exception as error:
            self.translation_failed.emit(str(error))
        else:
            self.translation_finished.emit(translated_text)
        finally:
            self.finished.emit()
