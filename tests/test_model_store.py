from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services import model_store


class ModelStoreTests(unittest.TestCase):
    def test_complete_speech_model_is_reused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            model_directory = Path(temporary_directory) / "speech" / "small"
            model_directory.mkdir(parents=True)
            for filename in ("config.json", "model.bin", "tokenizer.json"):
                (model_directory / filename).touch()

            with patch.object(
                model_store,
                "bundled_models_directory",
                return_value=Path(temporary_directory),
            ), patch.object(
                model_store,
                "writable_models_directory",
                return_value=Path(temporary_directory) / "writable",
            ):
                self.assertEqual(
                    model_store.speech_model_directory("small"),
                    model_directory,
                )

    def test_offline_bundle_does_not_download_missing_model(self) -> None:
        with patch.object(model_store, "is_offline_bundle", return_value=True):
            with self.assertRaises(model_store.ModelUnavailableError):
                model_store._require_download_allowed("missing-model")


if __name__ == "__main__":
    unittest.main()

