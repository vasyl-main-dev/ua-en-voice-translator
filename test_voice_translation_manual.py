from pathlib import Path
from time import perf_counter

from app.services.speech_recognizer import SpeechRecognizer
from app.services.translator import Translator


def main() -> None:
    audio_path = Path("recordings") / "microphone_test.wav"

    source_language = "uk"
    target_language = "en"

    speech_recognizer = SpeechRecognizer(
        model_size="small",
        device="cuda",
        compute_type="float16",
    )
    translator = Translator()

    processing_started_at = perf_counter()

    print("Розпізнавання мовлення...")

    recognition_started_at = perf_counter()

    recognized_text = speech_recognizer.transcribe(
        audio_path=audio_path,
        language=source_language,
    )

    recognition_time = perf_counter() - recognition_started_at

    if not recognized_text:
        print("Whisper не розпізнав мовлення")
        return

    print("Переклад тексту...")

    translation_started_at = perf_counter()

    translated_text = translator.translate(
        text=recognized_text,
        source_language=source_language,
        target_language=target_language,
    )

    translation_time = perf_counter() - translation_started_at
    total_time = perf_counter() - processing_started_at

    print()
    print(f"Оригінальний текст: {recognized_text}")
    print(f"Переклад: {translated_text}")
    print()
    print(f"Розпізнавання: {recognition_time:.2f} с")
    print(f"Переклад: {translation_time:.2f} с")
    print(f"Загальний час: {total_time:.2f} с")


if __name__ == "__main__":
    main()
