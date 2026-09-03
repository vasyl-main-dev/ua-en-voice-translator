from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIRECTORY = PROJECT_ROOT / "local_models" / "translation"

MODEL_NAMES = {
    ("uk", "en"): "Helsinki-NLP/opus-mt-uk-en",
    ("en", "uk"): "Helsinki-NLP/opus-mt-en-uk",
}


class Translator:
    def __init__(self) -> None:
        self.tokenizers = {}
        self.models = {}

    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        text = text.strip()

        if not text:
            return ""

        language_pair = (source_language, target_language)

        if language_pair not in MODEL_NAMES:
            raise ValueError(
                f"Непідтримуваний напрямок перекладу: "
                f"{source_language} → {target_language}"
            )

        tokenizer, model = self._get_model(language_pair)

        encoded_text = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        with torch.inference_mode():
            generated_tokens = model.generate(
                **encoded_text,
                max_length=256,
                num_beams=4,
            )

        translated_text = tokenizer.decode(
            generated_tokens[0],
            skip_special_tokens=True,
        )

        return translated_text

    def _get_model(self, language_pair: tuple[str, str]):
        if language_pair not in self.models:
            self._load_model(language_pair)

        tokenizer = self.tokenizers[language_pair]
        model = self.models[language_pair]

        return tokenizer, model

    def _load_model(self, language_pair: tuple[str, str]) -> None:
        model_name = MODEL_NAMES[language_pair]

        MODELS_DIRECTORY.mkdir(parents=True, exist_ok=True)

        print(f"Завантаження моделі: {model_name}")

        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=MODELS_DIRECTORY,
        )

        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            cache_dir=MODELS_DIRECTORY,
        )
        model.eval()

        self.tokenizers[language_pair] = tokenizer
        self.models[language_pair] = model

        print("Модель готова")
