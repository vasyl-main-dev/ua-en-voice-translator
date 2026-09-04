import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.core.runtime import detect_compute_profile


class DetectComputeProfileTests(unittest.TestCase):
    def test_cpu_can_be_forced(self) -> None:
        with patch.dict(
            os.environ,
            {"VOICE_TRANSLATOR_DEVICE": "cpu"},
        ):
            profile = detect_compute_profile()

        self.assertEqual(profile.device, "cpu")
        self.assertEqual(profile.compute_type, "int8")

    def test_auto_uses_cuda_when_ctranslate2_detects_gpu(self) -> None:
        fake_ctranslate2 = SimpleNamespace(
            get_cuda_device_count=lambda: 1
        )

        with (
            patch.dict(
                sys.modules,
                {"ctranslate2": fake_ctranslate2},
            ),
            patch.dict(
                os.environ,
                {"VOICE_TRANSLATOR_DEVICE": "auto"},
            ),
        ):
            profile = detect_compute_profile()

        self.assertEqual(profile.device, "cuda")
        self.assertEqual(profile.compute_type, "float16")

    def test_auto_falls_back_to_cpu_without_cuda(self) -> None:
        fake_ctranslate2 = SimpleNamespace(
            get_cuda_device_count=lambda: 0
        )

        with (
            patch.dict(
                sys.modules,
                {"ctranslate2": fake_ctranslate2},
            ),
            patch.dict(
                os.environ,
                {"VOICE_TRANSLATOR_DEVICE": "auto"},
            ),
        ):
            profile = detect_compute_profile()

        self.assertEqual(profile.device, "cpu")
        self.assertEqual(profile.compute_type, "int8")


if __name__ == "__main__":
    unittest.main()
