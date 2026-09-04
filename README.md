# UA ↔ EN Voice Translator

Desktop application for offline Ukrainian ↔ English text and voice
translation. The interface is built with PySide6, speech is recognized by
faster-whisper, and Helsinki-NLP models perform translation.

## Current modes

- manual text translation in both directions;
- continuous microphone translation until the user presses **Stop**;
- automatic NVIDIA CUDA detection with a safe CPU fallback;
- speech segmentation around pauses instead of rigid five-second borders;
- context-aware recognition with overlap protection;
- translation of complete sentences with NLLB-200;
- gradual display of recognized and translated phrases.

The CPU fallback works on Windows laptops with NVIDIA, AMD or Intel graphics,
and on computers without a discrete GPU. AMD GPU acceleration is not enabled:
those computers use the processor, because this CTranslate2 configuration
supports CUDA acceleration only on NVIDIA hardware.

## Requirements

- Windows 10 or 11 (64-bit);
- Python 3.14;
- a working microphone;
- internet access on the first launch to download AI models;
- approximately 6–10 GB of free disk space for dependencies and models.

After the models have been downloaded, recognition and translation work
offline.

The current release targets standard x86-64 laptops with Intel or AMD
processors. Windows on ARM is not supported yet.

## Installation

Create and activate a virtual environment first.

### Universal CPU profile (recommended)

Works on all supported Windows laptops:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### NVIDIA profile

Use this profile for a compatible NVIDIA GPU and CUDA acceleration:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-nvidia.txt
```

If the NVIDIA runtime or its DLLs cannot be loaded, the application
automatically retries Whisper on the CPU instead of terminating.

## Run

```powershell
python main.py
```

Choose the translation direction and press **Почати переклад**. The program
keeps recording while previous phrases are being processed. It normally ends
a fragment after about 700 ms of silence. Long uninterrupted speech is split
after 12 seconds with a short overlap, and repeated overlap words are removed.
Press **Stop** to finish recording and process the remaining queued audio.

The first phrase can take longer because Whisper and the translation model
are loaded lazily. NVIDIA mode uses Whisper `medium`; CPU mode uses Whisper
`small`. Translation uses `facebook/nllb-200-distilled-600M`. On CPU-only
computers, live results may lag behind speech; the exact delay depends on
processor performance.

## Runtime override

Automatic selection is the default. It can be overridden for diagnostics:

```powershell
$env:VOICE_TRANSLATOR_DEVICE = "cpu"
python main.py
```

Supported values are `auto`, `cpu` and `cuda`.

## Checks

Run lightweight automated checks:

```powershell
python -m unittest discover -s tests
```

Manual microphone and model checks remain available in the root directory.

## Version history

- `release/v0.1.0` — original verified record-then-translate application;
- `release/v0.2.0` — verified portable continuous translator;
- `feature/translation-quality` — pause-aware speech segmentation, adaptive
  Whisper models, recognition context and NLLB translation.
