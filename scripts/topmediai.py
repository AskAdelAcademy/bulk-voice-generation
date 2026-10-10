"""Only documented TopMediai contracts. Never log raw API responses."""
import json
import os
import urllib.error
import urllib.request
from local_settings import load_saved_key, SettingsError
from urllib.parse import urlsplit
from audio_codec import decoder_path, normalize_wav


class VoiceError(Exception):
    pass


class UncertainGeneration(VoiceError):
    """A billed POST may have completed; do not silently replay it."""


class GenerationRejected(VoiceError):
    """Verified provider rejection: no successful audio needs reconciliation."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise VoiceError("Unexpected API redirect; stopped without forwarding credentials.")


def payload(text, speaker, emotion=None):
    if not isinstance(text, str) or not 1 <= len(text) <= 500:
        raise VoiceError("Each speech request must contain 1 to 500 characters.")
    if not isinstance(speaker, str) or not speaker.strip():
        raise VoiceError("Choose a speaker from the current TopMediai voice list.")
    result = {"text": text, "speaker": speaker}
    if emotion:
        result["emotion"] = emotion
    return result


class TopMediai:
    def __init__(self, key=None):
        # Lazy access keeps offline lesson preparation independent of key storage.
        self._key = key

    @property
    def key(self):
        if self._key is not None:
            return self._key.strip()
        try:
            return os.environ.get("TOPMEDIAI_API_KEY", "").strip() or load_saved_key()
        except SettingsError as exc:
            raise VoiceError(str(exc)) from None

    def get(self, path):
        key = self.key
        if not key:
            raise VoiceError("Open Voice Setup, paste your TopMediai key into its private field, and choose Check connection and save. See references/setup.md.")
        if path not in ("voices_list", "get_api_key_info"):
            raise VoiceError("Unsupported API operation.")
        req = urllib.request.Request("https://api.topmediai.com/v1/" + path,
                                     headers={"x-api-key": key, "Accept": "application/json"})
        try:
            with urllib.request.build_opener(NoRedirect).open(req, timeout=45) as response:
                raw = response.read(10_000_001)
            if len(raw) > 10_000_000:
                raise VoiceError("API response exceeds the read limit.")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise VoiceError("Unexpected API response structure.")
            return result
        except urllib.error.HTTPError as exc:
            hints = {401: "Check your API key.", 403: "Check account permissions.",
                     429: "Rate limited; wait before trying again."}
            raise VoiceError(f"TopMediai HTTP {exc.code}. {hints.get(exc.code, 'Try again later or consult TopMediai support.')} Response details withheld.") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise VoiceError("Unable to reach TopMediai. Check the connection and try again.") from None
        except (ValueError, UnicodeError):
            raise VoiceError("TopMediai returned an unreadable response.") from None

    def check(self):
        result = self.get("get_api_key_info")
        if not all(type(result.get(k)) is int for k in ("key_status", "key_words_counts")):
            raise VoiceError("Account response did not match the documented schema.")
        # Never return the raw response: it contains the API key and personal data.
        return {k: result[k] for k in ("key_status", "key_words_counts")}

    def voices(self, query=""):
        rows = self.get("voices_list").get("Voice")
        if not isinstance(rows, list):
            raise VoiceError("Voice list did not match the documented schema.")
        safe = []
        for row in rows:
            if not isinstance(row, dict) or not all(isinstance(row.get(k), str) for k in ("speaker", "name", "Languagename")):
                raise VoiceError("Voice entry did not match the documented schema.")
            item = {k: row[k] for k in ("speaker", "name", "Languagename")}
            if query.casefold() in " ".join(item.values()).casefold():
                safe.append(item)
        return safe

    def ensure_synthesis_ready(self):
        if not decoder_path():
            raise VoiceError("Audio setup needs a decoder. Ask Codex to install imageio-ffmpeg using references/setup.md. No speech request was sent.")
        if not self.key:
            raise VoiceError("Open Voice Setup to connect your TopMediai account first.")

    def synthesize_wav(self, text, speaker, emotion=None):
        self.ensure_synthesis_ready()
        request = urllib.request.Request("https://api.topmediai.com/v1/text2speech",
            data=json.dumps(payload(text, speaker, emotion)).encode("utf-8"),
            headers={"x-api-key": self.key, "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with urllib.request.build_opener(NoRedirect).open(request, timeout=120) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError()
            result = json.loads(raw)
            # Observed on the official API in the authorized 2026-10-09 live test.
            if not isinstance(result, dict) or result.get("status") != 200:
                raise ValueError()
            url = result["data"]["oss_url"]
            return self.download_audio(url)
        except urllib.error.HTTPError as exc:
            if exc.code in (400, 401, 403, 422, 429):
                raise GenerationRejected(f"TopMediai rejected the request (HTTP {exc.code}). Check your key, credits, voice, or request limit.") from None
            raise UncertainGeneration("Speech request outcome is uncertain. Do not resend automatically.") from None
        except Exception:
            raise UncertainGeneration("Speech or audio download did not finish. It may have consumed credits; do not resend automatically.") from None

    def download_audio(self, url):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != "files.topmediai.com" or parsed.port not in (None, 443) or parsed.username or parsed.password:
            raise VoiceError("Unrecognized audio download host. Review the provider response before proceeding.")
        # Never send authentication headers to storage; do not follow redirects.
        try:
            with urllib.request.build_opener(NoRedirect).open(url, timeout=90) as response:
                data = response.read(25_000_001)
            if len(data) > 25_000_000:
                raise ValueError()
            return normalize_wav(data)
        except Exception:
            raise UncertainGeneration("Generated audio could not be downloaded or decoded; a new request may charge again.") from None
