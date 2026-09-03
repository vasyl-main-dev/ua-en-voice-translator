from app.services.translator import Translator


def main() -> None:
    translator = Translator()

    examples = [
        (
            "Привіт! Це перша перевірка нашого голосового перекладача.",
            "uk",
            "en",
        ),
        (
            "Hello! This is the first test of our voice translator.",
            "en",
            "uk",
        ),
    ]

    for original_text, source_language, target_language in examples:
        translated_text = translator.translate(
            text=original_text,
            source_language=source_language,
            target_language=target_language,
        )

        print(f"\nНапрямок: {source_language} → {target_language}")
        print(f"Оригінал: {original_text}")
        print(f"Переклад: {translated_text}")


if __name__ == "__main__":
    main()
