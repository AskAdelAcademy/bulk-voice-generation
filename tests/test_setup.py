import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import local_settings as settings
from topmediai import TopMediai


class SetupTests(unittest.TestCase):
    def test_environment_key_precedes_saved_key(self):
        with patch.dict(os.environ, {"TOPMEDIAI_API_KEY": "environment-fixture"}), patch("topmediai.load_saved_key", side_effect=AssertionError("Do not load saved key")):
            self.assertEqual(TopMediai().key, "environment-fixture")

    def test_saved_key_reused_without_restart(self):
        provider = TopMediai()
        with patch.dict(os.environ, {"TOPMEDIAI_API_KEY": ""}), patch("topmediai.load_saved_key", return_value="local-fixture"):
            self.assertEqual(provider.key, "local-fixture")

    def test_window_supplied_key_is_not_environment_mutation(self):
        with patch.dict(os.environ, {"TOPMEDIAI_API_KEY": "environment-fixture"}):
            self.assertEqual(TopMediai("window-fixture").key, "window-fixture")
            self.assertEqual(os.environ["TOPMEDIAI_API_KEY"], "environment-fixture")

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI")
    def test_encrypted_storage_voice_and_forget(self):
        test_root = ROOT / "outputs" / "test-workspaces"
        test_root.mkdir(parents=True, exist_ok=True)
        # Temporary directory is created only under this verified workspace root.
        with tempfile.TemporaryDirectory(dir=test_root) as folder:
            path = Path(folder)
            self.assertTrue(path.resolve().is_relative_to(test_root.resolve()))
            with patch.object(settings, "settings_dir", return_value=path):
                settings.save_key("offline-storage-fixture")
                self.assertNotIn(b"offline-storage-fixture", (path / "api-key.dpapi").read_bytes())
                self.assertEqual(settings.load_saved_key(), "offline-storage-fixture")
                voice = {"speaker": "voice-fixture", "name": "Test Voice", "language": "English"}
                settings.save_voice(voice)
                self.assertEqual(settings.load_voice(), voice)
                self.assertNotIn("offline-storage-fixture", (path / "voice.json").read_text())
                settings.forget_key()
                self.assertEqual(settings.load_saved_key(), "")
                self.assertEqual(settings.load_voice(), voice)

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI")
    def test_corrupt_encryption_is_rejected(self):
        with self.assertRaises(settings.SettingsError):
            settings.protect(b"not-encrypted-data", decrypt=True)


if __name__ == "__main__":
    unittest.main()
