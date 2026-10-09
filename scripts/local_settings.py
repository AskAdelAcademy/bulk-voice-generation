"""Windows user-protected key storage outside the skill/repository."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path


class SettingsError(Exception):
    pass


def settings_dir():
    if os.name != "nt" or not os.environ.get("LOCALAPPDATA"):
        raise SettingsError("The setup window's saved settings require Windows. Existing environment keys still work on other systems.")
    return Path(os.environ["LOCALAPPDATA"]) / "BulkVoiceGeneration"


class Blob(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def protect(data, decrypt=False):
    if os.name != "nt":
        raise SettingsError("Windows key protection is unavailable on this computer.")
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    operation = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    operation.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob),
                          ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    operation.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    try:
        # User scope: never set CRYPTPROTECT_LOCAL_MACHINE. No legacy DPAPI UI.
        if not operation(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output)):
            raise SettingsError("Windows could not unlock or protect the saved key. Enter it again in Voice Setup.")
        return ctypes.string_at(output.data, output.size)
    finally:
        ctypes.memset(buffer, 0, len(data))
        if output.data:
            ctypes.memset(output.data, 0, output.size)
            kernel.LocalFree(output.data)


def write_private(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".part")
    temp.write_bytes(data)
    temp.replace(path)


def save_key(key):
    key = key.strip()
    if not key or len(key) > 8192 or any(c.isspace() for c in key):
        raise SettingsError("Paste the API key by itself, without spaces or extra text.")
    write_private(settings_dir() / "api-key.dpapi", protect(key.encode("utf-8")))


def load_saved_key():
    if os.name != "nt":
        return ""
    path = settings_dir() / "api-key.dpapi"
    if not path.exists():
        return ""
    try:
        return protect(path.read_bytes(), decrypt=True).decode("utf-8")
    except (OSError, UnicodeError):
        raise SettingsError("The saved key could not be opened. Enter it again in Voice Setup.") from None


def forget_key():
    # One specific file only, outside the repository; no recursive deletion.
    (settings_dir() / "api-key.dpapi").unlink(missing_ok=True)


def load_voice():
    if os.name != "nt":
        return {}
    path = settings_dir() / "voice.json"
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or not all(isinstance(value.get(k), str) for k in ("speaker", "name", "language")):
            raise ValueError()
        return {k: value[k] for k in ("speaker", "name", "language")}
    except (OSError, ValueError):
        raise SettingsError("The saved voice could not be read. Choose it again in Voice Setup.") from None


def save_voice(voice):
    value = {k: voice[k] for k in ("speaker", "name", "language")}
    if not all(isinstance(v, str) and v.strip() for v in value.values()):
        raise SettingsError("Choose an available voice first.")
    write_private(settings_dir() / "voice.json", json.dumps(value, ensure_ascii=False).encode("utf-8"))
