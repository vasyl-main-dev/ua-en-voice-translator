import wave
from pathlib import Path

import numpy as np
import sounddevice as sd


class AudioRecorder:
    def __init__(
        self,
        sample_rate: int = 16_000,
        channels: int = 1,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels

        self.audio_frames: list[np.ndarray] = []
        self.stream: sd.InputStream | None = None

    @property
    def is_recording(self) -> bool:
        return self.stream is not None

    def start(self) -> None:
        if self.is_recording:
            raise RuntimeError("Запис уже виконується")

        self.audio_frames.clear()

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._audio_callback,
        )

        self.stream.start()

    def stop(self, output_path: Path) -> Path:
        if not self.is_recording:
            raise RuntimeError("Запис не був запущений")

        self.stream.stop()
        self.stream.close()
        self.stream = None

        if not self.audio_frames:
            raise RuntimeError("Не вдалося записати звук")

        audio_data = np.concatenate(
            self.audio_frames,
            axis=0,
        )

        audio_data = np.clip(audio_data, -1.0, 1.0)
        audio_int16 = (audio_data * 32_767).astype(np.int16)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with wave.open(str(output_path), "wb") as audio_file:
            audio_file.setnchannels(self.channels)
            audio_file.setsampwidth(2)
            audio_file.setframerate(self.sample_rate)
            audio_file.writeframes(audio_int16.tobytes())

        return output_path

    def _audio_callback(
        self,
        input_data: np.ndarray,
        frames: int,
        time,
        status,
    ) -> None:
        if status:
            print(f"Статус аудіозапису: {status}")

        self.audio_frames.append(input_data.copy())
