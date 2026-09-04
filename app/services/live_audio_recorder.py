from __future__ import annotations

from queue import Empty, Queue
from threading import Event

import numpy as np
import sounddevice as sd


class LiveAudioRecorder:
    """Continuously captures microphone frames into a thread-safe queue."""

    def __init__(
        self,
        sample_rate: int = 16_000,
        channels: int = 1,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self._frames: Queue[np.ndarray] = Queue()
        self._stream: sd.InputStream | None = None

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        if self.is_recording:
            raise RuntimeError("Безперервний запис уже виконується")

        self._clear_queue()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is None:
            return

        self._stream.stop()
        self._stream.close()
        self._stream = None

    def read_chunk(
        self,
        duration_seconds: float,
        stop_event: Event,
    ) -> np.ndarray:
        target_frame_count = int(self.sample_rate * duration_seconds)
        chunks: list[np.ndarray] = []
        collected_frame_count = 0

        while collected_frame_count < target_frame_count:
            if stop_event.is_set() and self._frames.empty():
                break

            try:
                frame = self._frames.get(timeout=0.1)
            except Empty:
                if stop_event.is_set():
                    break
                continue

            chunks.append(frame)
            collected_frame_count += len(frame)

        if not chunks:
            return np.empty((0,), dtype=np.float32)

        audio = np.concatenate(chunks, axis=0)
        return np.asarray(audio, dtype=np.float32).reshape(-1)

    def has_pending_audio(self) -> bool:
        return not self._frames.empty()

    def _clear_queue(self) -> None:
        while True:
            try:
                self._frames.get_nowait()
            except Empty:
                return

    def _audio_callback(
        self,
        input_data: np.ndarray,
        frames: int,
        time,
        status,
    ) -> None:
        del frames, time

        if status:
            print(f"Статус аудіозапису: {status}")

        self._frames.put(input_data.copy())
