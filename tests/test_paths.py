from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.paths import is_offline_bundle, writable_models_directory


class WritableModelsDirectoryTests(unittest.TestCase):
    def test_environment_override_has_priority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.dict(
                os.environ,
                {"VOICE_TRANSLATOR_MODELS_DIR": temporary_directory},
            ):
                self.assertEqual(
                    writable_models_directory(),
                    Path(temporary_directory).resolve(),
                )

    def test_offline_mode_is_read_from_package_manifest(self) -> None:
        with patch(
            "app.core.paths.package_manifest",
            return_value={"package_mode": "offline"},
        ):
            self.assertTrue(is_offline_bundle())
