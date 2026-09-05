from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.core.paths import is_frozen_application, package_manifest


@dataclass(frozen=True, slots=True)
class ComputeProfile:
    """CTranslate2 settings selected for the current computer."""

    device: str
    compute_type: str
    accelerator: str

    @property
    def description(self) -> str:
        if self.device == "cuda":
            return "NVIDIA CUDA (GPU)"
        return "CPU (працює з NVIDIA, AMD, Intel та без дискретної відеокарти)"


_dll_directory_handles: list[object] = []


def prepare_windows_dll_search_path() -> None:
    """Expose bundled PyTorch CUDA libraries to CTranslate2 on Windows.

    The NVIDIA dependency profile contains the CUDA runtime inside the
    PyTorch package. CPU installations may not have PyTorch's ``lib``
    directory or any CUDA DLLs, so this helper intentionally does nothing
    when they are absent.
    """

    if os.name != "nt":
        return

    try:
        import torch
    except (ImportError, OSError):
        return

    library_directory = Path(torch.__file__).resolve().parent / "lib"
    if not library_directory.exists():
        return

    library_path = str(library_directory)
    current_path = os.environ.get("PATH", "")
    path_entries = current_path.split(os.pathsep) if current_path else []

    if library_path not in path_entries:
        os.environ["PATH"] = os.pathsep.join(
            [library_path, *path_entries]
        )

    try:
        handle = os.add_dll_directory(library_path)
    except (AttributeError, FileNotFoundError, OSError):
        return

    # The handle must stay alive while CTranslate2 is using the DLLs.
    _dll_directory_handles.append(handle)


def detect_compute_profile() -> ComputeProfile:
    """Select CUDA when it is usable and otherwise return a safe CPU mode."""

    requested_device = os.environ.get(
        "VOICE_TRANSLATOR_DEVICE",
        "auto",
    ).strip().lower()

    if requested_device not in {"auto", "cpu", "cuda"}:
        raise ValueError(
            "VOICE_TRANSLATOR_DEVICE має бути auto, cpu або cuda"
        )

    if requested_device == "cpu":
        return cpu_compute_profile()

    packaged_profile = package_manifest().get("runtime_profile")
    if packaged_profile == "cpu" or (
        is_frozen_application() and packaged_profile != "cuda"
    ):
        if requested_device == "cuda":
            raise RuntimeError(
                "Цей універсальний інсталятор містить CPU-версію. "
                "Для CUDA потрібна окрема NVIDIA-збірка."
            )
        return cpu_compute_profile()

    prepare_windows_dll_search_path()

    try:
        import ctranslate2

        cuda_available = ctranslate2.get_cuda_device_count() > 0
    except (ImportError, OSError, RuntimeError):
        cuda_available = False

    if cuda_available:
        return ComputeProfile(
            device="cuda",
            compute_type="float16",
            accelerator="nvidia",
        )

    if requested_device == "cuda":
        raise RuntimeError(
            "CUDA запитано примусово, але сумісну NVIDIA GPU не знайдено"
        )

    return cpu_compute_profile()


def cpu_compute_profile() -> ComputeProfile:
    return ComputeProfile(
        device="cpu",
        compute_type="int8",
        accelerator="cpu",
    )
