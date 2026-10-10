import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from topmediai import TopMediai, VoiceError, GenerationRejected, UncertainGeneration


def response(body):
    mock = MagicMock()
    mock.__enter__.return_value.read.return_value = body
    return mock


class AudioContractTests(unittest.TestCase):
    def test_observed_response_and_key_separation(self):
        client = TopMediai("synthetic-test-key")
        opener = MagicMock()
        opener.open.side_effect = [response(json.dumps({"status": 200, "data": {"oss_url": "https://files.topmediai.com/test.wav"}}).encode()), response(b"ID3-audio-fixture")]
        with patch("topmediai.decoder_path", return_value="decoder"), patch("topmediai.urllib.request.build_opener", return_value=opener), patch("topmediai.normalize_wav", return_value=b"normalized-wav") as normalize:
            self.assertEqual(client.synthesize_wav("A lesson.", "speaker"), b"normalized-wav")
        request = opener.open.call_args_list[0].args[0]
        self.assertEqual(json.loads(request.data), {"text": "A lesson.", "speaker": "speaker"})
        self.assertEqual(opener.open.call_args_list[1].args[0], "https://files.topmediai.com/test.wav")
        normalize.assert_called_once_with(b"ID3-audio-fixture")

    def test_untrusted_download_destinations_rejected(self):
        with patch("topmediai.urllib.request.build_opener") as opener:
            for url in ("http://files.topmediai.com/a", "https://example.com/a", "https://user:pass@files.topmediai.com/a", "https://files.topmediai.com:8443/a"):
                with self.assertRaises(VoiceError):
                    TopMediai().download_audio(url)
            opener.assert_not_called()

    def test_timeout_is_uncertain_without_retry(self):
        opener = MagicMock()
        opener.open.side_effect = TimeoutError()
        with patch("topmediai.decoder_path", return_value="decoder"), patch("topmediai.urllib.request.build_opener", return_value=opener):
            with self.assertRaises(UncertainGeneration):
                TopMediai("synthetic-test-key").synthesize_wav("Test", "speaker")
        self.assertEqual(opener.open.call_count, 1)

    def test_explicit_http_rejection(self):
        opener = MagicMock()
        opener.open.side_effect = urllib.error.HTTPError("https://api.topmediai.com/v1/text2speech", 429, "limited", {}, io.BytesIO())
        with patch("topmediai.decoder_path", return_value="decoder"), patch("topmediai.urllib.request.build_opener", return_value=opener):
            with self.assertRaises(GenerationRejected):
                TopMediai("synthetic-test-key").synthesize_wav("Test", "speaker")
