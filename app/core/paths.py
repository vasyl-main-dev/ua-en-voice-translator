from __future__ import annotations

import os
import json
import sys
from pathlib import Path


APPLICATION_DIRECTORY_NAME = "UA-EN Voice Translator"
MODELS_DIRECTORY_ENVIRONMENT_VARIABLE = "VOICE_TRANSLATOR_MODELS_DIR"


def is_frozen_application() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    """Return the read-only directory containing packaged resources."""

    if is_frozen_application():
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parents[2]


def bundled_models_directory() -> Path:
    return resource_root() / "local_models"


def writable_models_directory() -> Path:
    """Return a stable writable model cache outside an installed app."""

    configured_directory = os.environ.get(
        MODELS_DIRECTORY_ENVIRONMENT_VARIABLE,
    )
    if configured_directory:
        return Path(configured_directory).expanduser().resolve()

    if not is_frozen_application():
        return resource_root() / "local_models"

    local_application_data = os.environ.get("LOCALAPPDATA")
    if local_application_data:
        return (
            Path(local_application_data)
            / APPLICATION_DIRECTORY_NAME
            / "models"
        )

    return Path.home() / ".ua-en-voice-translator" / "models"


def package_manifest_path() -> Path:
    return resource_root() / "package_manifest.json"


def package_manifest() -> dict[str, str]:
    path = package_manifest_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def is_offline_bundle() -> bool:
    return package_manifest().get("package_mode") == "offline"
