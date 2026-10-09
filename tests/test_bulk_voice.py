import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import bulk_voice as bulk
from topmediai import TopMediai, VoiceError, GenerationRejected, UncertainGeneration, payload


def tone():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 80)
    return buffer.getvalue()


class FakeProvider:
    def __init__(self, failure=None):
        self.calls = []
        self.failure = failure

    def ensure_synthesis_ready(self):
        pass

    def check(self):
        return {"key_words_counts": 100000, "key_status": 1}

    def voices(self):
        return [{"speaker": "offline-test"}]

    def synthesize_wav(self, text, speaker, emotion):
        self.calls.append(text)
        if self.failure and len(self.calls) == 2:
            raise self.failure("Private server body must never be saved")
        return tone()


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        test_root = ROOT / "outputs" / "test-workspaces"
        test_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=test_root)
        self.out = Path(self.temp.name) / "lesson"
        self.lesson = bulk.load_json(ROOT / "examples/six-section-lesson.json")

    def tearDown(self):
        self.assertTrue(Path(self.temp.name).resolve().is_relative_to((ROOT / "outputs" / "test-workspaces").resolve()))
        self.temp.cleanup()

    def prepare(self, lesson=None):
        return bulk.prepare(lesson or self.lesson, self.out, "offline-test", "Offline fixture")

    def test_lossless_chunking(self):
        for text in ("A word. " * 200, "字" * 1201, "A " * 600, "short"):
            parts = bulk.chunks(text)
            self.assertEqual("".join(parts), text)
            self.assertTrue(all(1 <= len(p) <= 500 for p in parts))

    def test_entire_lesson_validation_before_files(self):
        lesson = copy.deepcopy(self.lesson)
        lesson["sections"][-1]["transcript"] = ""
        with self.assertRaises(VoiceError):
            self.prepare(lesson)
        self.assertFalse(self.out.exists())

    def test_six_sections_and_resume(self):
        manifest = self.prepare()
        self.assertEqual(len(manifest["sections"]), 6)
        self.assertGreater(len(manifest["sections"][2]["chunks"]), 1)
        fake = FakeProvider()
        result = bulk.generate(self.out, fake)
        self.assertEqual(set(result["statuses"].values()), {"completed"})
        self.assertEqual(len(list(self.out.glob("*.wav"))), 6)
        expected = [c["text"] for r in manifest["sections"] for c in r["chunks"]]
        self.assertEqual(fake.calls, expected)
        count = len(fake.calls)
        bulk.generate(self.out, fake)
        self.assertEqual(len(fake.calls), count)
        for row in manifest["sections"]:
            with wave.open(str(self.out / row["audio_filename"]), "rb") as audio:
                self.assertEqual(audio.getnframes(), 80 * len(row["chunks"]))

    def test_rejected_section_preserves_successes(self):
        self.prepare()
        fake = FakeProvider(GenerationRejected)
        result = bulk.generate(self.out, fake)
        self.assertEqual(result["statuses"]["2"], "failed")
        self.assertEqual(result["statuses"]["6"], "completed")
        first = (self.out / "01-what-is-observation.wav").read_bytes()
        retry = FakeProvider()
        bulk.generate(self.out, retry, section=2)
        self.assertEqual(len(retry.calls), 1)
        self.assertEqual((self.out / "01-what-is-observation.wav").read_bytes(), first)
        self.assertNotIn("Private server", (self.out / "manifest.json").read_text())

    def test_uncertain_not_automatically_retried(self):
        self.prepare()
        result = bulk.generate(self.out, FakeProvider(UncertainGeneration))
        self.assertEqual(result["statuses"]["2"], "uncertain")
        retry = FakeProvider()
        bulk.generate(self.out, retry)
        self.assertEqual(retry.calls, [])
        result = bulk.generate(self.out, retry, retry_uncertain=True)
        self.assertEqual(set(result["statuses"].values()), {"completed"})

    def test_source_and_voice_change_detected(self):
        self.prepare()
        manifest = bulk.load_json(self.out / "manifest.json")
        manifest["sections"][0]["voice_used"]["speaker"] = "different"
        bulk.save_json(self.out / "manifest.json", manifest)
        with self.assertRaises(VoiceError):
            bulk.generate(self.out, FakeProvider())

    def test_raw_draft_requires_contextual_review(self):
        lesson = {"sections": [{"title": "Web", "transcript": "Read https://example.com and <b> in HTML."}]}
        manifest = self.prepare(lesson)
        self.assertEqual(manifest["sections"][0]["original_transcript"], lesson["sections"][0]["transcript"])
        self.assertIn("https://example.com", manifest["sections"][0]["narration_ready_transcript"])
        with self.assertRaises(VoiceError):
            bulk.generate(self.out, FakeProvider())

    def test_readonly_check_never_returns_key(self):
        with patch.object(TopMediai, "get", return_value={"x_api_key": "sensitive-fixture", "email": "private", "key_status": 1, "key_words_counts": 30}):
            result = TopMediai().check()
            self.assertEqual(result, {"key_status": 1, "key_words_counts": 30})

    def test_generation_blocked_before_network(self):
        self.prepare()
        with patch.object(TopMediai, "get", side_effect=AssertionError("Unexpected network call")):
            with self.assertRaisesRegex(VoiceError, "not enabled"):
                bulk.generate(self.out, TopMediai())

    def test_payload_and_invalid_audio(self):
        self.assertEqual(payload("Hello", "voice"), {"text": "Hello", "speaker": "voice"})
        with self.assertRaises(VoiceError):
            payload("a" * 501, "voice")
        with self.assertRaises(VoiceError):
            bulk.wav_info(b"<html>error</html>")


if __name__ == "__main__":
    unittest.main()
