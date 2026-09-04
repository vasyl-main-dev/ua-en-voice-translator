from pathlib import Path
from time import perf_counter

from app.services.speech_recognizer import SpeechRecognizer


def main() -> None:
    audio_path = Path("recordings") / "microphone_test.wav"

    recognizer = SpeechRecognizer(model_size="small")

    print(f"Режим обчислень: {recognizer.runtime_description}")

    started_at = perf_counter()

    recognized_text = recognizer.transcribe(
        audio_path=audio_path,
        language="uk",
    )

    elapsed_time = perf_counter() - started_at

    print(f"Аудіофайл: {audio_path.resolve()}")
    print(f"Розпізнаний текст: {recognized_text}")
    print(f"Час розпізнавання: {elapsed_time:.2f} с")


if __name__ == "__main__":
    main()
