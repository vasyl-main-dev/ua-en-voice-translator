"""PyInstaller runtime hook for the universal Windows distributions."""

import os


# Run before the application imports CTranslate2 or PyTorch. The universal
# installers contain CPU-only PyTorch and must not auto-select CUDA merely
# because an NVIDIA adapter is visible.
os.environ["VOICE_TRANSLATOR_DEVICE"] = "cpu"

