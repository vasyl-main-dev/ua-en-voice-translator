from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from faster_whisper.utils import download_model
from huggingface_hub import snapshot_download

from app.services.model_store import (
    DEFAULT_SPEECH_MODEL,
    TRANSLATION_MODEL_DIRECTORY_NAME,
    TRANSLATION_MODEL_NAME,
    WHISPER_REPOSITORIES,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download models for the universal offline installer.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination local_models directory.",
    )
    parser.add_argument(
        "--speech-model",
        choices=tuple(WHISPER_REPOSITORIES),
        default=DEFAULT_SPEECH_MODEL,
        help="Whisper model to include in the offline package.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    output_directory = arguments.output.resolve()
    speech_model = arguments.speech_model
    speech_directory = output_directory / "speech" / speech_model
    translation_directory = (
        output_directory
        / "translation"
        / TRANSLATION_MODEL_DIRECTORY_NAME
    )

    print(f"Downloading Whisper {speech_model}...")
    speech_directory.mkdir(parents=True, exist_ok=True)
    download_model(speech_model, output_dir=str(speech_directory))

    print("Downloading NLLB-200 distilled 600M...")
    translation_directory.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=TRANSLATION_MODEL_NAME,
        local_dir=translation_directory,
    )
    print(f"Offline models are ready in {output_directory}")


if __name__ == "__main__":
    main()
