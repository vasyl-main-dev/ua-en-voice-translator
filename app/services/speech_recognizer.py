from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.core.runtime import (
    ComputeProfile,
    cpu_compute_profile,
    detect_compute_profile,
    prepare_windows_dll_search_path,
)

if TYPE_CHECKING:
    import numpy as np


prepare_windows_dll_search_path()

from faster_whisper import WhisperModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPEECH_MODELS_DIRECTORY = PROJECT_ROOT / "local_models" / "speech"


class SpeechRecognizer:
    def __init__(
        self,
        model_size: str = "small",
        profile: ComputeProfile | None = None,
    ) -> None:
        self.model_size = model_size
        self.profile = profile or detect_compute_profile()
        self.model: WhisperModel | None = None
        self.fallback_reason: str | None = None

    @property
    def runtime_description(self) -> str:
        return self.profile.description

    def transcribe(
        self,
        audio_path: Path,
        language: str,
    ) -> str:
        if not audio_path.exists():
            raise FileNotFoundError(
                f"Аудіофайл не знайдено: {audio_path}"
            )

        return self._transcribe_audio(str(audio_path), language)

    def transcribe_samples(
        self,
        audio_samples: "np.ndarray",
        language: str,
    ) -> str:
        if audio_samples.size == 0:
            return ""

        return self._transcribe_audio(audio_samples, language)

    def _transcribe_audio(self, audio, language: str) -> str:
        model = self._get_model()

        segments, _ = model.transcribe(
            audio=audio,
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

    def _get_model(self) -> WhisperModel:
        if self.model is None:
            self.model = self._load_model_with_fallback()

        return self.model

    def _load_model_with_fallback(self) -> WhisperModel:
        SPEECH_MODELS_DIRECTORY.mkdir(parents=True, exist_ok=True)

        try:
            return self._create_model(self.profile)
        except (OSError, RuntimeError) as error:
            if self.profile.device != "cuda":
                raise

            self.fallback_reason = str(error)
            print(
                "Не вдалося запустити Whisper через CUDA. "
                "Автоматично перемикаємося на CPU."
            )
            self.profile = cpu_compute_profile()
            return self._create_model(self.profile)

    def _create_model(self, profile: ComputeProfile) -> WhisperModel:
        print(f"Завантаження Whisper-моделі: {self.model_size}")

        model = WhisperModel(
            model_size_or_path=self.model_size,
            device=profile.device,
            compute_type=profile.compute_type,
            download_root=str(SPEECH_MODELS_DIRECTORY),
        )

        print(
            "Whisper готовий: "
            f"device={profile.device}, "
            f"compute_type={profile.compute_type}"
        )
        return model
