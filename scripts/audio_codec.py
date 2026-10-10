"""Decode provider audio by its content, never its filename extension."""
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave


def decoder_path():
    installed = shutil.which("ffmpeg")
    if installed:
        return installed
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        folder = Path(os.environ["LOCALAPPDATA"]) / "BulkVoiceGeneration/runtime/imageio_ffmpeg/binaries"
        binaries = sorted(folder.glob("ffmpeg*.exe"))
        if binaries:
            return str(binaries[0])
    return None


def normalize_wav(data):
    decoder = decoder_path()
    if not decoder:
        raise RuntimeError("Audio decoder is not installed.")
    with tempfile.TemporaryDirectory(prefix="bulk-voice-decode-") as folder:
        output = Path(folder) / "decoded.wav"
        result = subprocess.run([decoder, "-nostdin", "-v", "error", "-protocol_whitelist", "pipe,file",
            "-i", "pipe:0", "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(output)],
            input=data, capture_output=True, timeout=90,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        if result.returncode or not output.exists():
            raise RuntimeError("Provider audio could not be decoded.")
        normalized = output.read_bytes()
    with wave.open(io.BytesIO(normalized), "rb") as audio:
        if audio.getnframes() < 1 or audio.getcomptype() != "NONE":
            raise RuntimeError("Decoded audio is empty or unsupported.")
    return normalized
