"""Prepare lessons and checkpoint section audio. Python standard library only."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import unicodedata
import wave

from topmediai import TopMediai, VoiceError, UncertainGeneration, GenerationRejected
from local_settings import load_voice, SettingsError


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def save_json(path, value):
    temp = path.with_suffix(path.suffix + ".part")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def slug(title):
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:70].rstrip("-") or "section"


def draft(text):
    # Do not strip markup or URLs: they can be the subject being taught.
    return re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def findings(text):
    patterns = {
        "links or website addresses": r"https?://|www\.|\[[^\]]+\]\(|\b[\w-]+\.(?:com|org|net|edu|io)\b",
        "HTML or angle-bracket notation": r"<[^>]+>",
        "Markdown, code, or bullet formatting": r"[`*_#]|(?m:^[ \t]*(?:[-+]|\d+[.)])\s)",
        "paths": r"[A-Za-z]:\\|(?:/\w+){2,}",
        "parentheses": r"[()]",
        "abbreviations": r"\b[A-Z]{2,}\b",
        "symbols or repeated punctuation": r"[=<>@&%]|[!?.,]{2,}",
        "visual instructions": r"(?i)\b(?:see|look at|shown|on screen|slide|diagram|chart)\b",
    }
    return [label for label, pattern in patterns.items() if re.search(pattern, text)]


def chunks(text, limit=500):
    """Lossless split: joining chunks exactly reproduces the source text."""
    result = []
    while len(text) > limit:
        head = text[:limit]
        sentence = list(re.finditer(r"[.!?。！？]\s+|\n+", head))
        spaces = list(re.finditer(r"\s+", head))
        cut = sentence[-1].end() if sentence else spaces[-1].end() if spaces else limit
        result.append(text[:cut])
        text = text[cut:]
    if text:
        result.append(text)
    return result


def prepare(lesson, out, speaker="", voice_name="", emotion=None):
    if not isinstance(lesson, dict) or not isinstance(lesson.get("sections"), list) or not lesson["sections"]:
        raise VoiceError("Lesson JSON needs a nonempty sections array.")
    rows, numbers = [], set()
    width = max(2, len(str(len(lesson["sections"]))))
    for position, section in enumerate(lesson["sections"], 1):
        if not isinstance(section, dict):
            raise VoiceError(f"Section {position} must be an object.")
        number = section.get("number", position)
        if type(number) not in (int, str) or not str(number).strip() or str(number) in numbers:
            raise VoiceError(f"Section {position} has an empty, invalid, or duplicate number.")
        numbers.add(str(number))
        title, original = section.get("title"), section.get("transcript")
        if not all(isinstance(t, str) and t.strip() for t in (title, original)):
            raise VoiceError(f"Section {position} needs a title and nonempty transcript.")
        narration = section.get("narration_ready", draft(original))
        if not isinstance(narration, str) or not narration.strip():
            raise VoiceError(f"Section {position} has empty narration.")
        reviewed = section.get("cleanup_reviewed") is True and "narration_ready" in section
        rows.append({"position": position, "section_number": number, "section_title": title,
                     "original_transcript": original, "narration_ready_transcript": narration,
                     "cleanup_reviewed": reviewed, "findings": findings(narration),
                     "audio_filename": f"{position:0{width}d}-{slug(title)}.wav",
                     "voice_used": {"speaker": speaker, "name": voice_name, "emotion": emotion},
                     "status": "pending", "chunks": [{"text": t, "status": "pending"} for t in chunks(narration)]})
    manifest = {"schema_version": 1, "lesson_title": lesson.get("title", "Lesson"), "sections": rows}
    manifest["plan_hash"] = plan_hash(manifest)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise VoiceError("Output folder is not empty. Resume it with generate, or prepare into a new folder.")
    save_json(out / "manifest.json", manifest)
    return manifest


def plan_hash(manifest):
    keys = ("position", "section_number", "section_title", "original_transcript", "narration_ready_transcript", "cleanup_reviewed", "audio_filename", "voice_used")
    return digest([{k: row[k] for k in keys} for row in manifest["sections"]])


def validated_manifest(out):
    manifest = load_json(out / "manifest.json")
    if manifest.get("schema_version") != 1 or manifest.get("plan_hash") != plan_hash(manifest):
        raise VoiceError("Prepared content changed. Prepare the updated lesson into a new output folder.")
    for row in manifest["sections"]:
        if Path(row["audio_filename"]).name != row["audio_filename"] or not re.fullmatch(r"\d+-[a-z0-9-]+\.wav", row["audio_filename"]):
            raise VoiceError("Unsafe output filename in manifest.")
        if [c["text"] for c in row["chunks"]] != chunks(row["narration_ready_transcript"]):
            raise VoiceError("Chunk plan changed. Prepare again into a new folder.")
    return manifest


def wav_info(data):
    try:
        with wave.open(io.BytesIO(data), "rb") as audio:
            params = (audio.getnchannels(), audio.getsampwidth(), audio.getframerate())
            frames = audio.readframes(audio.getnframes())
            if audio.getcomptype() != "NONE" or not frames or len(frames) != audio.getnframes() * params[0] * params[1]:
                raise ValueError()
            return params, frames
    except (wave.Error, EOFError, ValueError):
        raise VoiceError("Audio is not valid, nonempty PCM WAV.") from None


def join_wav(files, target):
    expected = None
    temp = target.with_suffix(".wav.part")
    with wave.open(str(temp), "wb") as audio:
        for path in files:
            params, frames = wav_info(path.read_bytes())
            if expected is None:
                expected = params
                audio.setnchannels(params[0])
                audio.setsampwidth(params[1])
                audio.setframerate(params[2])
            if params != expected:
                raise VoiceError("Chunk audio formats differ; adapter must normalize PCM before assembly.")
            audio.writeframes(frames)
    temp.replace(target)


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(out, provider, section=None, retry_uncertain=False, dry_run=False):
    out = Path(out)
    manifest = validated_manifest(out)
    rows = manifest["sections"]
    if section is not None and not 1 <= section <= len(rows):
        raise VoiceError("Section position is outside the lesson.")
    summary = {"sections": len(rows), "characters": sum(len(r["narration_ready_transcript"]) for r in rows),
               "requests": sum(len(r["chunks"]) for r in rows),
               "review_needed": [r["position"] for r in rows if not r["cleanup_reviewed"]]}
    if dry_run:
        return summary
    if summary["review_needed"]:
        raise VoiceError("Narration cleanup needs contextual review. Edit lesson JSON and prepare a new folder.")
    if any(not r["voice_used"]["speaker"] for r in rows):
        raise VoiceError("Choose a voice before generation and prepare a new folder.")
    provider.ensure_synthesis_ready()  # Must stop here while response contract is unresolved.
    provider.check()
    available = {v["speaker"] for v in provider.voices()}
    if any(r["voice_used"]["speaker"] not in available for r in rows):
        raise VoiceError("A selected voice is not in the current voice list.")
    cache = out / ".chunks"
    cache.mkdir(exist_ok=True)
    for row in rows:
        if section is not None and row["position"] != section:
            continue
        target = out / row["audio_filename"]
        if row["status"] == "completed":
            if target.exists() and file_hash(target) == row.get("audio_sha256"):
                continue
            raise VoiceError("Completed audio is missing or changed. Restore it or use a new output folder.")
        files = []
        try:
            for index, chunk in enumerate(row["chunks"], 1):
                path = cache / f"{row['position']:04d}-{index:04d}.wav"
                if chunk["status"] == "completed":
                    if not path.exists() or file_hash(path) != chunk.get("sha256"):
                        raise VoiceError("Saved chunk is missing or changed; restore it before retrying.")
                    wav_info(path.read_bytes())
                else:
                    if chunk["status"] in ("in_progress", "uncertain") and not retry_uncertain:
                        raise UncertainGeneration("Previous request outcome is uncertain.")
                    chunk["status"] = "in_progress"
                    row["status"] = "in_progress"
                    save_json(out / "manifest.json", manifest)
                    voice = row["voice_used"]
                    data = provider.synthesize_wav(chunk["text"], voice["speaker"], voice["emotion"])
                    wav_info(data)
                    temp = path.with_suffix(".part")
                    temp.write_bytes(data)
                    temp.replace(path)
                    chunk.update(status="completed", sha256=file_hash(path))
                    save_json(out / "manifest.json", manifest)
                files.append(path)
            join_wav(files, target)
            row.update(status="completed", audio_sha256=file_hash(target))
            row.pop("error", None)
        except GenerationRejected:
            for c in row["chunks"]:
                if c["status"] == "in_progress":
                    c["status"] = "failed"
            row.update(status="failed", error="Provider rejected this section. Correct the cause, then retry this section.")
        except Exception:
            # Suppress provider exceptions: response bodies can contain credentials.
            uncertain = any(c["status"] in ("in_progress", "uncertain") for c in row["chunks"])
            for c in row["chunks"]:
                if c["status"] == "in_progress":
                    c["status"] = "uncertain"
            row["status"] = "uncertain" if uncertain else "failed"
            row["error"] = "Request outcome uncertain; explicit retry may charge again." if uncertain else "Audio assembly or saved-chunk validation failed; completed files preserved."
        save_json(out / "manifest.json", manifest)
        if row["status"] == "uncertain":
            break  # Do not keep spending after ambiguous provider failures.
    return {"statuses": {str(r["position"]): r["status"] for r in rows}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("configuration", help="Report only whether a key is configured and the saved voice")
    voices = sub.add_parser("voices")
    voices.add_argument("--query", default="")
    prep = sub.add_parser("prepare")
    prep.add_argument("lesson")
    prep.add_argument("--output", required=True)
    prep.add_argument("--speaker", default="")
    prep.add_argument("--voice-name", default="")
    prep.add_argument("--emotion")
    gen = sub.add_parser("generate")
    gen.add_argument("output")
    gen.add_argument("--section", type=int)
    gen.add_argument("--dry-run", action="store_true")
    gen.add_argument("--retry-uncertain", action="store_true")
    args = parser.parse_args()
    provider = TopMediai()
    try:
        if args.command == "check":
            result = provider.check()
        elif args.command == "configuration":
            result = {"key_configured": bool(provider.key), "voice": load_voice()}
        elif args.command == "voices":
            result = provider.voices(args.query)
        elif args.command == "prepare":
            voice = load_voice() if not args.speaker else {}
            prepare(load_json(args.lesson), args.output, args.speaker or voice.get("speaker", ""),
                    args.voice_name or voice.get("name", ""), args.emotion)
            result = generate(args.output, provider, dry_run=True)
        else:
            result = generate(args.output, provider, args.section, args.retry_uncertain, args.dry_run)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if "statuses" in result and any(v != "completed" for v in result["statuses"].values()):
            return 2
        return 0
    except (VoiceError, SettingsError) as exc:
        print(str(exc), file=sys.stderr)
    except (OSError, ValueError, KeyError, TypeError):
        print("Unable to read or validate lesson/output files. Check the JSON schema and folder permissions.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
