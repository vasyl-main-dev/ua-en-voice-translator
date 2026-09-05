from __future__ import annotations

from pathlib import Path

from app.core.paths import (
    bundled_models_directory,
    is_offline_bundle,
    package_manifest,
    writable_models_directory,
)


TRANSLATION_MODEL_NAME = "facebook/nllb-200-distilled-600M"
TRANSLATION_MODEL_DIRECTORY_NAME = "nllb-200-distilled-600M"
DEFAULT_SPEECH_MODEL = "medium"
WHISPER_REPOSITORIES = {
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large-v3": "Systran/faster-whisper-large-v3",
}


def configured_speech_model() -> str:
    model_name = package_manifest().get(
        "speech_model",
        DEFAULT_SPEECH_MODEL,
    )
    if model_name not in WHISPER_REPOSITORIES:
        raise ValueError(
            f"Непідтримувана Whisper-модель у пакеті: {model_name}"
        )
    return model_name


class ModelUnavailableError(RuntimeError):
    pass


def speech_model_directory(model_size: str) -> Path:
    if model_size not in WHISPER_REPOSITORIES:
        raise ValueError(f"Непідтримувана Whisper-модель: {model_size}")

    relative_directory = Path("speech") / model_size
    return _resolve_existing_model(relative_directory) or (
        writable_models_directory() / relative_directory
    )


def translation_model_directory() -> Path:
    relative_directory = (
        Path("translation") / TRANSLATION_MODEL_DIRECTORY_NAME
    )
    return _resolve_existing_model(relative_directory) or (
        writable_models_directory() / relative_directory
    )


def ensure_speech_model(model_size: str) -> Path:
    destination = speech_model_directory(model_size)
    if _speech_model_is_complete(destination):
        return destination
    _require_download_allowed(model_size)

    from faster_whisper.utils import download_model

    destination.mkdir(parents=True, exist_ok=True)
    download_model(model_size, output_dir=str(destination))
    if not _speech_model_is_complete(destination):
        raise ModelUnavailableError(
            f"Whisper {model_size} завантажено не повністю"
        )
    return destination


def ensure_translation_model() -> Path:
    destination = translation_model_directory()
    if _translation_model_is_complete(destination):
        return destination
    _require_download_allowed(TRANSLATION_MODEL_NAME)

    from huggingface_hub import snapshot_download

    destination.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=TRANSLATION_MODEL_NAME,
        local_dir=destination,
    )
    if not _translation_model_is_complete(destination):
        raise ModelUnavailableError(
            "Модель NLLB-200 завантажено не повністю"
        )
    return destination


def _resolve_existing_model(relative_directory: Path) -> Path | None:
    candidates = (
        bundled_models_directory() / relative_directory,
        writable_models_directory() / relative_directory,
    )
    for candidate in candidates:
        if (
            _speech_model_is_complete(candidate)
            or _translation_model_is_complete(candidate)
        ):
            return candidate
    return None


def _speech_model_is_complete(directory: Path) -> bool:
    return all(
        (directory / filename).is_file()
        for filename in ("config.json", "model.bin", "tokenizer.json")
    )


def _translation_model_is_complete(directory: Path) -> bool:
    has_weights = any(
        (directory / filename).is_file()
        for filename in (
            "model.safetensors",
            "pytorch_model.bin",
            "model.safetensors.index.json",
            "pytorch_model.bin.index.json",
        )
    )
    return (directory / "config.json").is_file() and has_weights


def _require_download_allowed(model_name: str) -> None:
    if not is_offline_bundle():
        return
    raise ModelUnavailableError(
        "Офлайн-пакет не містить потрібної моделі "
        f"{model_name}. Перевстановіть повний офлайн-пакет."
    )
