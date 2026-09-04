from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class SpeechSegment:
    audio: np.ndarray
    overlaps_previous: bool = False


class SpeechSegmenter:
    """Build speech fragments around pauses instead of fixed time borders."""

    def __init__(
        self,
        sample_rate: int = 16_000,
        minimum_rms: float = 0.006,
        silence_seconds: float = 0.7,
        minimum_speech_seconds: float = 0.6,
        maximum_segment_seconds: float = 12.0,
        pre_roll_seconds: float = 0.25,
        forced_overlap_seconds: float = 0.6,
    ) -> None:
        self.sample_rate = sample_rate
        self.minimum_rms = minimum_rms
        self.silence_sample_count = int(sample_rate * silence_seconds)
        self.minimum_sample_count = int(
            sample_rate * minimum_speech_seconds
        )
        self.maximum_sample_count = int(
            sample_rate * maximum_segment_seconds
        )
        self.pre_roll_sample_count = int(sample_rate * pre_roll_seconds)
        self.overlap_sample_count = int(
            sample_rate * forced_overlap_seconds
        )

        self._pre_roll: deque[np.ndarray] = deque()
        self._pre_roll_size = 0
        self._segment_frames: list[np.ndarray] = []
        self._segment_size = 0
        self._silence_size = 0
        self._speech_size = 0
        self._active = False
        self._overlaps_previous = False
        self._noise_rms = 0.002

    def add_frame(self, frame: np.ndarray) -> list[SpeechSegment]:
        samples = np.asarray(frame, dtype=np.float32).reshape(-1)
        if samples.size == 0:
            return []

        rms = float(np.sqrt(np.mean(np.square(samples))))
        speech_threshold = max(self.minimum_rms, self._noise_rms * 3.0)
        contains_speech = rms >= speech_threshold

        if not self._active:
            if contains_speech:
                self._start_segment()
            else:
                self._noise_rms = (
                    self._noise_rms * 0.95 + rms * 0.05
                )
                self._remember_pre_roll(samples)
                return []

        self._segment_frames.append(samples)
        self._segment_size += samples.size

        if contains_speech:
            self._speech_size += samples.size
            self._silence_size = 0
        else:
            self._silence_size += samples.size

        if self._segment_size >= self.maximum_sample_count:
            return [self._finish_segment(force_overlap=True)]

        if (
            self._silence_size >= self.silence_sample_count
            and self._speech_size >= self.minimum_sample_count
        ):
            return [self._finish_segment(force_overlap=False)]

        return []

    def flush(self) -> list[SpeechSegment]:
        if (
            not self._active
            or self._speech_size < self.minimum_sample_count
        ):
            self._reset_segment()
            return []

        return [self._finish_segment(force_overlap=False)]

    def _start_segment(self) -> None:
        self._segment_frames = list(self._pre_roll)
        self._segment_size = self._pre_roll_size
        self._pre_roll.clear()
        self._pre_roll_size = 0
        self._silence_size = 0
        self._speech_size = 0
        self._active = True

    def _finish_segment(self, force_overlap: bool) -> SpeechSegment:
        audio = np.concatenate(self._segment_frames).astype(
            np.float32,
            copy=False,
        )
        result = SpeechSegment(
            audio=audio,
            overlaps_previous=self._overlaps_previous,
        )

        if force_overlap:
            overlap = audio[-self.overlap_sample_count :].copy()
            self._segment_frames = [overlap]
            self._segment_size = overlap.size
            self._silence_size = 0
            self._speech_size = overlap.size
            self._active = True
            self._overlaps_previous = True
        else:
            self._reset_segment()

        return result

    def _reset_segment(self) -> None:
        self._segment_frames = []
        self._segment_size = 0
        self._silence_size = 0
        self._speech_size = 0
        self._active = False
        self._overlaps_previous = False

    def _remember_pre_roll(self, samples: np.ndarray) -> None:
        self._pre_roll.append(samples)
        self._pre_roll_size += samples.size

        while (
            self._pre_roll
            and self._pre_roll_size > self.pre_roll_sample_count
        ):
            removed = self._pre_roll.popleft()
            self._pre_roll_size -= removed.size


class SentenceBuffer:
    """Keeps incomplete text until a complete sentence is available."""

    SENTENCE_PATTERN = re.compile(r".+?[.!?…]+(?=\s|$)")

    def __init__(self, maximum_characters: int = 350) -> None:
        self.maximum_characters = maximum_characters
        self._buffer = ""

    def add(self, text: str) -> list[str]:
        clean_text = text.strip()
        if not clean_text:
            return []

        self._buffer = " ".join(
            part for part in (self._buffer, clean_text) if part
        )
        sentences = self.SENTENCE_PATTERN.findall(self._buffer)

        if sentences:
            last_sentence = sentences[-1]
            end = self._buffer.rfind(last_sentence) + len(last_sentence)
            self._buffer = self._buffer[end:].strip()

        if len(self._buffer) >= self.maximum_characters:
            sentences.append(self._buffer)
            self._buffer = ""

        return [sentence.strip() for sentence in sentences]

    def flush(self) -> list[str]:
        if not self._buffer:
            return []

        remaining = self._buffer
        self._buffer = ""
        return [remaining]


def remove_word_overlap(previous_text: str, current_text: str) -> str:
    """Remove repeated leading words introduced by overlapping audio."""

    previous_words = previous_text.split()
    current_words = current_text.split()
    maximum_overlap = min(20, len(previous_words), len(current_words))

    for overlap_size in range(maximum_overlap, 0, -1):
        previous_tail = previous_words[-overlap_size:]
        current_head = current_words[:overlap_size]

        if [_normalise(word) for word in previous_tail] == [
            _normalise(word) for word in current_head
        ]:
            return " ".join(current_words[overlap_size:]).strip()

    return current_text.strip()


def _normalise(word: str) -> str:
    return re.sub(r"[^\w'-]", "", word, flags=re.UNICODE).casefold()
