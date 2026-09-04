from __future__ import annotations

from threading import Event

from PySide6.QtCore import QObject, Signal, Slot

from app.services.live_audio_recorder import LiveAudioRecorder
from app.services.speech_recognizer import SpeechRecognizer
from app.services.speech_segmentation import (
    SentenceBuffer,
    SpeechSegment,
    SpeechSegmenter,
    remove_word_overlap,
)
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
    ) -> None:
        super().__init__()
        self.speech_recognizer = speech_recognizer
        self.translator = translator
        self.source_language = source_language
        self.target_language = target_language
        self._stop_event = Event()
        self._recorder = LiveAudioRecorder(sample_rate=16_000)
        self._segmenter = SpeechSegmenter(sample_rate=16_000)
        self._sentence_buffer = SentenceBuffer()
        self._transcript = ""

    def request_stop(self) -> None:
        """Thread-safe stop request callable directly from the GUI thread."""

        self._stop_event.set()

    @Slot()
    def run(self) -> None:
        try:
            self._recorder.start()
            self.recording_started.emit()
            self.stage_changed.emit(
                "Слухаємо мовлення та визначаємо паузи..."
            )

            while not self._stop_event.is_set():
                frame = self._recorder.read_frame(
                    stop_event=self._stop_event,
                )
                if frame is not None:
                    self._process_segments(
                        self._segmenter.add_frame(frame)
                    )

            self._recorder.stop()

            while self._recorder.has_pending_audio():
                frame = self._recorder.read_frame(
                    stop_event=self._stop_event,
                )
                if frame is not None:
                    self._process_segments(
                        self._segmenter.add_frame(frame)
                    )

            self._process_segments(self._segmenter.flush())
            self._translate_sentences(self._sentence_buffer.flush())

        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self._recorder.stop()
            self.finished.emit()

    def _process_segments(
        self,
        segments: list[SpeechSegment],
    ) -> None:
        for segment in segments:
            self._process_segment(segment)

    def _process_segment(self, segment: SpeechSegment) -> None:
        self.stage_changed.emit("Розпізнавання завершеної фрази...")
        recognized_text = self.speech_recognizer.transcribe_samples(
            audio_samples=segment.audio,
            language=self.source_language,
            initial_prompt=self._context_prompt(),
        )

        if not recognized_text:
            self.stage_changed.emit("Слухаємо далі...")
            return

        if segment.overlaps_previous:
            recognized_text = remove_word_overlap(
                previous_text=self._transcript,
                current_text=recognized_text,
            )

        if not recognized_text:
            return

        self._transcript = " ".join(
            part for part in (self._transcript, recognized_text) if part
        )
        self.recognized.emit(recognized_text)
        self._translate_sentences(
            self._sentence_buffer.add(recognized_text)
        )
        self.stage_changed.emit("Слухаємо далі...")

    def _translate_sentences(self, sentences: list[str]) -> None:
        for sentence in sentences:
            self.stage_changed.emit("Переклад завершеного речення...")
            translated_text = self.translator.translate(
                text=sentence,
                source_language=self.source_language,
                target_language=self.target_language,
            )
            self.translated.emit(translated_text)

    def _context_prompt(self) -> str | None:
        if not self._transcript:
            return None

        words = self._transcript.split()
        return " ".join(words[-40:])
