from pathlib import Path

from app.services.speech_recognizer import SpeechRecognizer


def main() -> None:
    audio_path = Path("recordings") / "microphone_test.wav"

    recognizer = SpeechRecognizer(
        model_size="small",
        device="cpu",
        compute_type="int8",
    )

    recognized_text = recognizer.transcribe(
        audio_path=audio_path,
        language="uk",
    )

    print(f"Аудіофайл: {audio_path.resolve()}")
    print(f"Розпізнаний текст: {recognized_text}")


if __name__ == "__main__":
    main()
