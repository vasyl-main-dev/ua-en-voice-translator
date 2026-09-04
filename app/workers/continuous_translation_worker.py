from __future__ import annotations

from threading import Event

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

from app.services.live_audio_recorder import LiveAudioRecorder
from app.services.speech_recognizer import SpeechRecognizer
from app.services.translator import Translator


class ContinuousTranslationWorker(QObject):
    recording_started = Signal()
    recognized = Signal(str)
    translated = Signal(str)
    stage_changed = Signal(str)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        speech_recognizer: SpeechRecognizer,
        translator: Translator,
        source_language: str,
        target_language: str,
        chunk_seconds: float = 5.0,
        minimum_chunk_seconds: float = 0.5,
    ) -> None:
        super().__init__()
        self.speech_recognizer = speech_recognizer
        self.translator = translator
        self.source_language = source_language
        self.target_language = target_language
        self.chunk_seconds = chunk_seconds
        self.minimum_sample_count = int(
            16_000 * minimum_chunk_seconds
        )
        self._stop_event = Event()
        self._recorder = LiveAudioRecorder(sample_rate=16_000)

    def request_stop(self) -> None:
        """Thread-safe stop request callable directly from the GUI thread."""

        self._stop_event.set()

    @Slot()
    def run(self) -> None:
        try:
            self._recorder.start()
            self.recording_started.emit()
            self.stage_changed.emit(
                "Слухаємо мовлення та перекладаємо фрагментами..."
            )

            while not self._stop_event.is_set():
                audio = self._recorder.read_chunk(
                    duration_seconds=self.chunk_seconds,
                    stop_event=self._stop_event,
                )
                self._process_chunk(audio)

            self._recorder.stop()

            while self._recorder.has_pending_audio():
                audio = self._recorder.read_chunk(
                    duration_seconds=self.chunk_seconds,
                    stop_event=self._stop_event,
                )
                self._process_chunk(audio)

        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self._recorder.stop()
            self.finished.emit()

    def _process_chunk(self, audio: np.ndarray) -> None:
        if audio.size < self.minimum_sample_count:
            return

        self.stage_changed.emit("Розпізнавання фрагмента...")
        recognized_text = self.speech_recognizer.transcribe_samples(
            audio_samples=audio,
            language=self.source_language,
        )

        if not recognized_text:
            self.stage_changed.emit("Слухаємо далі...")
            return

        self.recognized.emit(recognized_text)
        self.stage_changed.emit("Переклад фрагмента...")

        translated_text = self.translator.translate(
            text=recognized_text,
            source_language=self.source_language,
            target_language=self.target_language,
        )
        self.translated.emit(translated_text)
        self.stage_changed.emit("Слухаємо далі...")
