from __future__ import annotations

import gc
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from app.core.runtime import ComputeProfile, detect_compute_profile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIRECTORY = PROJECT_ROOT / "local_models" / "translation"
MODEL_NAME = "facebook/nllb-200-distilled-600M"
LANGUAGE_CODES = {
    "uk": "ukr_Cyrl",
    "en": "eng_Latn",
}


class Translator:
    def __init__(
        self,
        profile: ComputeProfile | None = None,
    ) -> None:
        self.profile = profile or detect_compute_profile()
        self.device = self._select_device()
        self.tokenizer = None
        self.model = None
        self.fallback_reason: str | None = None

    @property
    def runtime_description(self) -> str:
        device_name = "GPU" if self.device == "cuda" else "CPU"
        return f"NLLB-200 ({device_name})"

    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        text = text.strip()
        if not text:
            return ""

        self._validate_language_pair(source_language, target_language)
        tokenizer, model = self._get_model()
        tokenizer.src_lang = LANGUAGE_CODES[source_language]

        encoded_text = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        encoded_text = {
            name: tensor.to(self.device)
            for name, tensor in encoded_text.items()
        }
        target_token_id = tokenizer.convert_tokens_to_ids(
            LANGUAGE_CODES[target_language]
        )

        with torch.inference_mode():
            generated_tokens = model.generate(
                **encoded_text,
                forced_bos_token_id=target_token_id,
                max_new_tokens=256,
                num_beams=5,
                no_repeat_ngram_size=3,
            )

        return tokenizer.decode(
            generated_tokens[0],
            skip_special_tokens=True,
        )

    def _get_model(self):
        if self.model is None or self.tokenizer is None:
            self._load_model_with_fallback()

        return self.tokenizer, self.model

    def _load_model_with_fallback(self) -> None:
        MODELS_DIRECTORY.mkdir(parents=True, exist_ok=True)
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            cache_dir=MODELS_DIRECTORY,
            src_lang=LANGUAGE_CODES["uk"],
        )

        try:
            self.model = self._create_model(self.device)
        except (OSError, RuntimeError) as error:
            if self.device != "cuda":
                raise

            self.fallback_reason = str(error)
            print(
                "Не вдалося завантажити NLLB через CUDA. "
                "Автоматично перемикаємо переклад на CPU."
            )
            self.model = None
            gc.collect()
            torch.cuda.empty_cache()
            self.device = "cpu"
            self.model = self._create_model(self.device)

    def _create_model(self, device: str):
        dtype = torch.float16 if device == "cuda" else torch.float32
        print(f"Завантаження моделі перекладу: {MODEL_NAME}")

        model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_NAME,
            cache_dir=MODELS_DIRECTORY,
            dtype=dtype,
        )
        model.to(device)
        model.eval()
        print(f"Модель перекладу готова: device={device}")
        return model

    def _select_device(self) -> str:
        if self.profile.device == "cuda" and torch.cuda.is_available():
            return "cuda"
        return "cpu"

    @staticmethod
    def _validate_language_pair(
        source_language: str,
        target_language: str,
    ) -> None:
        if (
            source_language not in LANGUAGE_CODES
            or target_language not in LANGUAGE_CODES
            or source_language == target_language
        ):
            raise ValueError(
                "Непідтримуваний напрямок перекладу: "
                f"{source_language} → {target_language}"
            )
