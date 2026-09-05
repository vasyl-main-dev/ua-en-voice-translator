from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.core.runtime import (
    ComputeProfile,
    cpu_compute_profile,
    detect_compute_profile,
    prepare_windows_dll_search_path,
)
from app.services.model_store import ensure_speech_model

if TYPE_CHECKING:
    import numpy as np


prepare_windows_dll_search_path()

from faster_whisper import WhisperModel


class SpeechRecognizer:
    def __init__(
        self,
        model_size: str | None = None,
        profile: ComputeProfile | None = None,
    ) -> None:
        self.profile = profile or detect_compute_profile()
        self.model_size = model_size or self._recommended_model_size()
        self.model: WhisperModel | None = None
        self.fallback_reason: str | None = None

    @property
    def runtime_description(self) -> str:
        return f"{self.profile.description}, Whisper {self.model_size}"

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
        initial_prompt: str | None = None,
    ) -> str:
        if audio_samples.size == 0:
            return ""

        return self._transcribe_audio(
            audio_samples,
            language,
            initial_prompt=initial_prompt,
        )

    def _transcribe_audio(
        self,
        audio,
        language: str,
        initial_prompt: str | None = None,
    ) -> str:
        try:
            return self._transcribe_with_current_model(
                audio,
                language,
                initial_prompt,
            )
        except (OSError, RuntimeError) as error:
            # CTranslate2 can postpone loading CUDA DLLs until the first
            # inference. Constructor-only fallback is therefore not enough.
            if self.profile.device != "cuda":
                raise
            self._switch_to_cpu(error)
            return self._transcribe_with_current_model(
                audio,
                language,
                initial_prompt,
            )

    def _transcribe_with_current_model(
        self,
        audio,
        language: str,
        initial_prompt: str | None,
    ) -> str:
        model = self._get_model()
        segments, _ = model.transcribe(
            audio=audio,
            language=language,
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=initial_prompt,
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
        try:
            return self._create_model(self.profile)
        except (OSError, RuntimeError) as error:
            if self.profile.device != "cuda":
                raise
            self._switch_to_cpu(error)
            return self._create_model(self.profile)

    def _switch_to_cpu(self, error: Exception) -> None:
        self.fallback_reason = str(error)
        print(
            "Не вдалося запустити Whisper через CUDA. "
            "Автоматично перемикаємося на CPU. "
            f"Причина: {error}"
        )
        self.model = None
        self.profile = cpu_compute_profile()
        # Keep the already downloaded model. In particular, a CUDA failure
        # must not silently replace Whisper medium with the less accurate
        # small model. Medium can also run on CPU with int8, although slower.

    def _recommended_model_size(self) -> str:
        return "medium"

    def _create_model(self, profile: ComputeProfile) -> WhisperModel:
        print(f"Завантаження Whisper-моделі: {self.model_size}")
        model_directory = ensure_speech_model(self.model_size)

        model = WhisperModel(
            model_size_or_path=str(model_directory),
            device=profile.device,
            compute_type=profile.compute_type,
            local_files_only=True,
        )

        print(
            "Whisper готовий: "
            f"device={profile.device}, "
            f"compute_type={profile.compute_type}"
        )
        return model
