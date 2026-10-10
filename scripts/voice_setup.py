"""Private, no-terminal Windows setup for Bulk Voice Generation."""
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

from local_settings import SettingsError, save_key, forget_key, load_voice, save_voice
from topmediai import TopMediai, VoiceError


def filter_voices(voices, query="", language="All languages"):
    words = query.casefold().split()
    matches = [v for v in voices
               if (language == "All languages" or v["Languagename"] == language)
               and all(word in (v["name"] + " " + v["Languagename"]).casefold() for word in words)]
    return sorted(matches, key=lambda v: (v["name"].casefold(), v["Languagename"].casefold(), v["speaker"]))


class SetupWindow:
    def __init__(self, root):
        self.root = root
        root.title("Bulk Voice Generation — Setup")
        root.geometry("780x880")
        root.minsize(700, 820)
        self.events = queue.Queue()
        self.busy = False
        self.current = []
        self.catalog = []
        self.catalog_loaded = False
        self.page = 0
        self.page_size = 50
        self.verified_key = None
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Set up your lesson voice", font=("Segoe UI", 19, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Connect your TopMediai account, then choose a voice. No commands needed.", wraplength=650).pack(anchor="w", pady=(8, 14))
        ttk.Label(frame, text="Save your account and voice here, then return to Codex to generate narration.", wraplength=650).pack(anchor="w", pady=(0, 18))
        ttk.Button(frame, text="1. Open TopMediai to get my key", command=lambda: webbrowser.open("https://www.topmediai.com/api/text-to-speech-api/")).pack(anchor="w")
        activation_note = tk.Frame(frame, background="#FFF3CD", highlightbackground="#B77900", highlightthickness=2, padx=12, pady=10)
        activation_note.pack(fill="x", pady=(10, 0))
        tk.Label(activation_note, text="IMPORTANT: API activation not working?", background="#FFF3CD", foreground="#663C00", font=("Segoe UI", 12, "bold"), anchor="w", justify="left").pack(fill="x")
        tk.Label(activation_note, text="If Click Activate does nothing or you see Unknown creator:\n1. Log out while on the TopMediai API page.\n2. Log back in FROM THAT SAME PAGE using your usual login method.\n3. Click Activate again.", background="#FFF3CD", foreground="#3D2B00", font=("Segoe UI", 10), wraplength=620, anchor="w", justify="left").pack(fill="x", pady=(6, 0))
        ttk.Label(frame, text="2. Paste your API key here (hidden). Leave blank to reuse a configured key.", wraplength=650).pack(anchor="w", pady=(14, 5))
        self.key = tk.StringVar()
        ttk.Entry(frame, textvariable=self.key, show="•").pack(fill="x")
        ttk.Label(frame, text="Saved with Windows encryption for your account, outside lesson files. Never paste your key into chat.", wraplength=650).pack(anchor="w", pady=5)
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=6)
        self.connect_button = ttk.Button(row, text="Check connection and save", command=self.connect)
        self.connect_button.pack(side="left")
        self.forget_button = ttk.Button(row, text="Forget saved key", command=self.forget)
        self.forget_button.pack(side="left", padx=8)
        ttk.Label(frame, text="3. Find a voice by language or name", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(14, 5))
        row = ttk.Frame(frame)
        row.pack(fill="x")
        self.query = tk.StringVar(value="English")
        search = ttk.Entry(row, textvariable=self.query)
        search.pack(side="left", fill="x", expand=True)
        search.bind("<Return>", lambda event: self.find_voices())
        self.find_button = ttk.Button(row, text="Find voices", command=self.find_voices)
        self.find_button.pack(side="left", padx=(8, 0))
        ttk.Label(frame, text="Type part of a name, language, or accent shown in the voice list. Results update as you type.", wraplength=650).pack(anchor="w", pady=5)
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Label(row, text="Language / accent:").pack(side="left")
        self.language = tk.StringVar(value="All languages")
        self.language_box = ttk.Combobox(row, textvariable=self.language, state="readonly", values=["All languages"])
        self.language_box.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(row, text="Clear filters", command=self.clear_filters).pack(side="left")
        self.results_label = tk.StringVar(value="Click Find voices once to load the available voices.")
        ttk.Label(frame, textvariable=self.results_label).pack(anchor="w", pady=(8, 0))
        row = ttk.Frame(frame)
        row.pack(fill="both", expand=True, pady=8)
        self.listbox = tk.Listbox(row, height=7, exportselection=False)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(row, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=(0, 8))
        self.previous_button = ttk.Button(row, text="Previous 50", command=lambda: self.move_page(-1), state="disabled")
        self.previous_button.pack(side="left")
        self.next_button = ttk.Button(row, text="Next 50", command=lambda: self.move_page(1), state="disabled")
        self.next_button.pack(side="left", padx=8)
        self.refresh_button = ttk.Button(row, text="Refresh voice list", command=lambda: self.find_voices(refresh=True))
        self.refresh_button.pack(side="right")
        row = ttk.Frame(frame)
        row.pack(fill="x")
        self.save_button = ttk.Button(row, text="Save voice", command=self.choose)
        self.save_button.pack(side="left")
        self.save_close_button = ttk.Button(row, text="Save voice and close", command=lambda: self.choose(close_after=True))
        self.save_close_button.pack(side="left", padx=8)
        ttk.Label(frame, text="After saving, you can close this window. Codex remembers your settings.", wraplength=650).pack(anchor="w", pady=(6, 0))
        self.status = tk.StringVar(value="Start by connecting your account. No speech credits are used by this setup window.")
        ttk.Label(frame, textvariable=self.status, wraplength=650).pack(anchor="w", pady=12)
        self.selected = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.selected, wraplength=650).pack(anchor="w")
        self.buttons = [self.connect_button, self.forget_button, self.find_button, self.save_button, self.save_close_button, self.refresh_button]
        self.query.trace_add("write", self.filters_changed)
        self.language.trace_add("write", self.filters_changed)
        try:
            voice = load_voice()
            if voice:
                self.selected.set("Saved voice: " + voice["name"])
        except SettingsError:
            self.status.set("Please choose your voice again; the saved choice could not be read.")
        root.after(100, self.poll)

    def start(self, worker):
        if self.busy:
            return
        self.busy = True
        for button in self.buttons:
            button.configure(state="disabled")
        self.status.set("Connecting to TopMediai…")
        def run():
            try:
                self.events.put((True, worker()))
            except (VoiceError, SettingsError) as exc:
                self.events.put((False, str(exc)))
            except Exception:
                self.events.put((False, "Setup could not finish. Check your internet connection and local storage permissions, then try again."))
        threading.Thread(target=run, daemon=True).start()

    def connect(self):
        entered = self.key.get().strip()
        if entered and os.environ.get("TOPMEDIAI_API_KEY", "").strip() and entered != os.environ["TOPMEDIAI_API_KEY"].strip():
            self.status.set("A different key is already configured for Codex. Leave this field blank to reuse it, or ask your instructor to remove the old setting first.")
            return
        self.key.set("")
        def worker():
            provider = TopMediai(entered or None)
            info = provider.check()
            if entered:
                save_key(entered)
            return ("connected", (provider.key, info["key_words_counts"]))
        self.start(worker)

    def find_voices(self, refresh=False):
        if self.catalog_loaded and not refresh:
            self.filters_changed()
            return
        self.start(lambda: ("voices", TopMediai(self.verified_key).voices()))

    def clear_filters(self):
        self.query.set("")
        self.language.set("All languages")

    def filters_changed(self, *args):
        self.page = 0
        self.render_results()

    def move_page(self, direction):
        self.page += direction
        self.render_results()

    def render_results(self):
        if not self.catalog_loaded:
            return
        matches = filter_voices(self.catalog, self.query.get(), self.language.get())
        self.page = max(0, min(self.page, max(0, (len(matches) - 1) // self.page_size)))
        start = self.page * self.page_size
        self.current = matches[start:start + self.page_size]
        self.listbox.delete(0, "end")
        for voice in self.current:
            self.listbox.insert("end", voice["name"] + " — " + voice["Languagename"])
        self.previous_button.configure(state="normal" if self.page else "disabled")
        self.next_button.configure(state="normal" if start + self.page_size < len(matches) else "disabled")
        self.results_label.set(f"{len(matches):,} matches — showing {start + 1}–{start + len(self.current)}. Refine your search to narrow the list." if matches else "No matches. Try a shorter name, another language, or Clear filters.")

    def poll(self):
        try:
            ok, result = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            for button in self.buttons:
                button.configure(state="normal")
            if not ok:
                self.status.set(result)
            elif result[0] == "connected":
                self.verified_key, remaining = result[1]
                self.status.set(f"Account check succeeded. Reported remaining characters: {remaining:,}. Now choose a voice below. Speech generation still needs a live test.")
            else:
                self.catalog = result[1]
                self.catalog_loaded = True
                languages = ["All languages"] + sorted({v["Languagename"] for v in self.catalog}, key=str.casefold)
                self.language_box.configure(values=languages)
                if self.language.get() not in languages:
                    self.language.set("All languages")
                self.filters_changed()
                self.status.set("Voice list loaded. Search by name and filter by language, then select a voice and click Save voice.")
        self.root.after(100, self.poll)

    def choose(self, close_after=False):
        selection = self.listbox.curselection()
        if not selection:
            self.status.set("Select a voice from the list first.")
            return
        voice = self.current[selection[0]]
        try:
            save_voice({"speaker": voice["speaker"], "name": voice["name"], "language": voice["Languagename"]})
        except (SettingsError, OSError):
            self.status.set("The voice could not be saved. Check your local storage permissions.")
            return
        self.selected.set("Saved voice: " + voice["name"])
        self.status.set("Voice saved successfully. You can close this window and return to Codex. Your settings will be reused for your next lesson.")
        messagebox.showinfo("Voice saved", f"Your voice choice, {voice['name']}, has been saved.\n\nThis window does not need to stay open. Return to Codex and say: My voice is set up.", parent=self.root)
        if close_after:
            self.root.destroy()

    def forget(self):
        try:
            forget_key()
            self.verified_key = None
            self.key.set("")
            self.status.set("Saved key removed. Any separately configured environment key remains available to Codex.")
        except (SettingsError, OSError):
            self.status.set("The saved key could not be removed. Check local storage permissions.")


def main():
    root = tk.Tk()
    if os.name != "nt":
        root.withdraw()
        messagebox.showinfo("Windows setup", "This setup window currently supports Windows. Ask Codex to help configure your account on this computer.")
        root.destroy()
        return
    SetupWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
