import unittest

import numpy as np

from app.services.speech_segmentation import (
    SentenceBuffer,
    SpeechSegmenter,
    remove_word_overlap,
)


class SpeechSegmenterTests(unittest.TestCase):
    def test_segment_finishes_after_a_pause(self) -> None:
        segmenter = SpeechSegmenter(sample_rate=1_000)
        silence = np.zeros(100, dtype=np.float32)
        speech = np.full(100, 0.05, dtype=np.float32)

        segments = []
        for _ in range(3):
            segments.extend(segmenter.add_frame(silence))
        for _ in range(8):
            segments.extend(segmenter.add_frame(speech))
        for _ in range(8):
            segments.extend(segmenter.add_frame(silence))

        self.assertEqual(len(segments), 1)
        self.assertGreaterEqual(segments[0].audio.size, 1_500)
        self.assertFalse(segments[0].overlaps_previous)

    def test_forced_long_segment_overlaps_the_next_one(self) -> None:
        segmenter = SpeechSegmenter(
            sample_rate=1_000,
            maximum_segment_seconds=1.0,
            minimum_speech_seconds=0.2,
            forced_overlap_seconds=0.2,
        )
        speech = np.full(100, 0.05, dtype=np.float32)

        segments = []
        for _ in range(13):
            segments.extend(segmenter.add_frame(speech))
        segments.extend(segmenter.flush())

        self.assertEqual(len(segments), 2)
        self.assertFalse(segments[0].overlaps_previous)
        self.assertTrue(segments[1].overlaps_previous)


class SentenceBufferTests(unittest.TestCase):
    def test_keeps_incomplete_sentence_until_it_is_finished(self) -> None:
        buffer = SentenceBuffer()

        self.assertEqual(buffer.add("Сьогодні ми тестуємо"), [])
        self.assertEqual(
            buffer.add("оновлену програму."),
            ["Сьогодні ми тестуємо оновлену програму."],
        )

    def test_flush_returns_remaining_text(self) -> None:
        buffer = SentenceBuffer()
        buffer.add("Незавершена фраза")

        self.assertEqual(buffer.flush(), ["Незавершена фраза"])


class RemoveWordOverlapTests(unittest.TestCase):
    def test_removes_repeated_words_from_overlapped_audio(self) -> None:
        result = remove_word_overlap(
            previous_text="Ми тестуємо нову програму",
            current_text="нову програму для перекладу тексту",
        )

        self.assertEqual(result, "для перекладу тексту")


if __name__ == "__main__":
    unittest.main()
