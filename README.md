# Bulk Voice Generation

A Codex skill for turning educational lessons into one numbered narration WAV per section using TopMediai. It keeps original transcripts, prepares natural spoken versions, uses a consistent selected voice, and records resumable progress.

## Install and start

Tell Codex:

> Use skill-installer to install https://github.com/AskAdelAcademy/bulk-voice-generation as bulk-voice-generation. The skill is at repository root (path .).

On your next turn, attach a lesson and say:

> Use $bulk-voice-generation to narrate this lesson. Help me set up my voice if needed.

Students do not need PowerShell, JSON, or voice IDs. Codex runs helpers and opens the private Windows setup window if settings are missing. It includes language/name search, save confirmation, and Save voice and close. Credentials are encrypted for the Windows user outside lesson/skill folders. Environment keys are also supported. See [the student guide](STUDENT-GUIDE.md).

## Requirements and output

- Python 3.10+ and Tkinter for the Windows setup window.
- A TopMediai API key and sufficient API credits, separate from the web TTS subscription.
- FFmpeg decoder; Codex can install imageio-ffmpeg into a local runtime. See [setup](references/setup.md).
- Internet access for API calls and audio downloads.

Output is WAV. Requests are limited to 500 characters; longer sections are split and decoded chunks assembled. Both transcript versions, voice, filenames, chunk progress, and status are kept in manifest.json. Completed files are preserved on retry. Uncertain outcomes require explicit retry authorization because they might charge twice.

Integration follows official request documentation and an authorized live response. TopMediai returned MP3 content with a WAV filename; the decoder handles this. The adapter supports the observed status: 200 / data.oss_url response on files.topmediai.com. See [API details](references/topmediai-api.md). Listen to a short sample before a large lesson.

## Technical checks for Codex and instructors

Students can ask Codex to prepare or narrate the included six-section example. The helper accepts normalized JSON authored by Codex after reading the complete lesson.

~~~sh
python scripts/bulk_voice.py configuration
python scripts/bulk_voice.py check
python scripts/bulk_voice.py prepare examples/six-section-lesson.json --output outputs/my-test
python scripts/bulk_voice.py generate outputs/my-test --dry-run
python scripts/bulk_voice.py generate outputs/my-test
python -m unittest discover -s tests -v
~~~

Prepare reuses the saved voice unless an explicit speaker is supplied. Use a new folder when changing narration or voice. Generate resumes unfinished work; --section 2 selects one section. Do not run concurrent generators on the same folder. Dry runs do not synthesize speech.

The 24 offline tests cover ordering, lossless splitting, review requirements, WAV assembly, retries, credentials, response handling, download restrictions, search, and saving. Generated lessons, credentials, local packages, and developer artifacts are ignored by Git.

Live verification on 2026-10-09 generated all six example sections with the saved Red-Glasses voice (seven requests, 1,325 narration characters). All six files decoded as PCM WAV, including the long section assembled from two chunks. A subsequent resume run completed without calling synthesis again. A separate short probe confirmed the response format. This is a technical generation check; listeners should still review pronunciation and teaching suitability before distributing their own lessons.

## Files

SKILL.md contains agent instructions; agents/openai.yaml supplies metadata. Scripts implement preparation, API access, decoding, setup, and encrypted settings. References explain setup, cleanup, and API behavior. Examples include a six-section lesson. Tests run offline. Voice Setup.vbs is an optional manual launcher; Codex normally opens setup for the student.
