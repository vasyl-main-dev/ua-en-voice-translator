from __future__ import annotations

import json
import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files


project_root = Path(SPECPATH).parent
package_mode = os.environ.get(
    "VOICE_TRANSLATOR_PACKAGE_MODE",
    "online",
).lower()
supported_package_modes = {
    "online",
    "offline",
    "nvidia-large-online",
    "nvidia-large-offline",
}
if package_mode not in supported_package_modes:
    raise ValueError(
        "Unsupported VOICE_TRANSLATOR_PACKAGE_MODE: "
        f"{package_mode}"
    )

is_nvidia_package = package_mode.startswith("nvidia-large-")
is_offline_package = package_mode.endswith("offline")
speech_model = "large-v3" if is_nvidia_package else "medium"
runtime_profile = "cuda" if is_nvidia_package else "cpu"

datas = [
    (
        str(project_root / "app" / "ui" / "styles.qss"),
        "app/ui",
    ),
]
binaries = []
hiddenimports = []

manifest_path = project_root / "build" / "package_manifest.json"
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(
    json.dumps(
        {
            "package_mode": package_mode,
            "runtime_profile": runtime_profile,
            "speech_model": speech_model,
            "translation_model": "facebook/nllb-200-distilled-600M",
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
datas.append((str(manifest_path), "."))

for dependency in (
    "av",
    "ctranslate2",
    "faster_whisper",
    "sentencepiece",
    "sounddevice",
    "tokenizers",
    "torch",
    "transformers",
):
    dependency_datas, dependency_binaries, dependency_hiddenimports = (
        collect_all(dependency)
    )
    datas += dependency_datas
    binaries += dependency_binaries
    hiddenimports += dependency_hiddenimports

datas += collect_data_files("certifi")

if is_offline_package:
    models_directory = project_root / "build" / "offline_models"
    if not models_directory.is_dir():
        raise FileNotFoundError(
            "Offline models are missing. Run download_offline_models.py first."
        )
    datas.append((str(models_directory), "local_models"))

application_names = {
    "online": "UA-EN-Voice-Translator-Online",
    "offline": "UA-EN-Voice-Translator-Offline",
    "nvidia-large-online": "UA-EN-Voice-Translator-NVIDIA-Large-Online",
    "nvidia-large-offline": "UA-EN-Voice-Translator-NVIDIA-Large-Offline",
}
application_name = application_names[package_mode]

runtime_hooks = []
if not is_nvidia_package:
    runtime_hooks.append(
        str(project_root / "packaging" / "runtime_force_cpu.py")
    )

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=application_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=application_name,
)
