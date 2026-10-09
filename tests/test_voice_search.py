from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from voice_setup import filter_voices, SetupWindow


class VoiceSearchTests(unittest.TestCase):
    def setUp(self):
        self.voices = [
            {"speaker": "a", "name": "Alice", "Languagename": "English (US)"},
            {"speaker": "b", "name": "Alice", "Languagename": "English (UK)"},
            {"speaker": "c", "name": "Bruno", "Languagename": "French"},
        ]

    def test_multiple_words_and_case(self):
        result = filter_voices(self.voices, "ALIce us")
        self.assertEqual([v["speaker"] for v in result], ["a"])

    def test_language_and_query_combined(self):
        self.assertEqual([v["speaker"] for v in filter_voices(self.voices, "alice", "English (UK)")], ["b"])
        self.assertEqual(filter_voices(self.voices, "alice", "French"), [])

    def test_clear_search_and_no_match(self):
        self.assertEqual(len(filter_voices(self.voices, "  ")), 3)
        self.assertEqual(filter_voices(self.voices, "missing"), [])

    def test_pagination_and_selected_voice(self):
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            with patch("voice_setup.load_voice", return_value={}):
                window = SetupWindow(root)
            window.catalog = [{"speaker": str(i), "name": f"Voice {i:03}", "Languagename": "English"} for i in range(101)]
            window.catalog_loaded = True
            window.render_results()
            self.assertEqual(window.listbox.size(), 50)
            window.move_page(1)
            self.assertEqual(window.current[0]["speaker"], "50")
            window.listbox.selection_set(0)
            with patch("voice_setup.save_voice") as save, patch("voice_setup.messagebox.showinfo") as confirmation:
                window.choose()
                self.assertEqual(save.call_args.args[0]["speaker"], "50")
                confirmation.assert_called_once()
            window.query.set("100")
            self.assertEqual(window.page, 0)
            self.assertEqual(window.listbox.size(), 1)
            self.assertEqual(window.current[0]["speaker"], "100")
            window.query.set("no matches")
            self.assertEqual(window.listbox.size(), 0)
            window.clear_filters()
            self.assertEqual(window.listbox.size(), 50)
        finally:
            root.destroy()

    def test_save_close_only_after_success(self):
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            with patch("voice_setup.load_voice", return_value={}):
                window = SetupWindow(root)
            window.catalog = self.voices
            window.catalog_loaded = True
            window.render_results()
            with patch.object(root, "destroy") as close, patch("voice_setup.messagebox.showinfo") as confirmation:
                window.choose(close_after=True)
                close.assert_not_called()
                window.listbox.selection_set(0)
                with patch("voice_setup.save_voice", side_effect=OSError("Cannot save")):
                    window.choose(close_after=True)
                close.assert_not_called()
                confirmation.assert_not_called()
                with patch("voice_setup.save_voice"):
                    window.choose(close_after=True)
                confirmation.assert_called_once()
                close.assert_called_once()
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
