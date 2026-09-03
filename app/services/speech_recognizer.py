import os
from pathlib import Path

import torch


TORCH_LIBRARY_DIRECTORY = (
    Path(torch.__file__).resolve().parent / "lib"
)

_dll_directory_handle = None

if os.name == "nt" and TORCH_LIBRARY_DIRECTORY.exists():
    _dll_directory_handle = os.add_dll_directory(
        str(TORCH_LIBRARY_DIRECTORY)
    )

    os.environ["PATH"] = (
        f"{TORCH_LIBRARY_DIRECTORY}"
        f"{os.pathsep}"
        f"{os.environ.get('PATH', '')}"
    )


from faster_whisper import WhisperModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPEECH_MODELS_DIRECTORY = PROJECT_ROOT / "local_models" / "speech"


class SpeechRecognizer:
    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

        self.model: WhisperModel | None = None

    def transcribe(
        self,
        audio_path: Path,
        language: str,
    ) -> str:
        if not audio_path.exists():
            raise FileNotFoundError(
                f"Аудіофайл не знайдено: {audio_path}"
            )

        model = self._get_model()

        segments, _ = model.transcribe(
            audio=str(audio_path),
            language=language,
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )

        recognized_parts = [
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        ]

        return " ".join(recognized_parts)

    def _get_model(self) -> WhisperModel | None:
        if self.model is None:
            SPEECH_MODELS_DIRECTORY.mkdir(
                parents=True,
                exist_ok=True,
            )

            print(
                f"Завантаження Whisper-моделі: {self.model_size}"
            )

            self.model = WhisperModel(
                model_size_or_path=self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(SPEECH_MODELS_DIRECTORY),
            )

            print(
                f"Whisper готовий: "
                f"device={self.device}, "
                f"compute_type={self.compute_type}"
            )

        return self.model
