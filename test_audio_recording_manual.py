from pathlib import Path

from app.services.audio_recorder import AudioRecorder


def main() -> None:
    recorder = AudioRecorder()

    print("Запис розпочато. Скажіть декілька речень.")
    print("Натисніть Enter, щоб завершити запис.")

    recorder.start()
    input()

    output_path = recorder.stop(
        Path("recordings") / "microphone_test.wav"
    )

    print(f"Запис збережено: {output_path.resolve()}")


if __name__ == "__main__":
    main()
