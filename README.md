# Bulk Voice Generation — Preview

A reusable Codex skill for teachers and course creators. This folder is independent of `bulk-images-generation`.

**Current status:** lesson preparation and offline workflow tests are implemented. Authentication, account checking, voice listing, and TTS request fields follow the official API documentation. **Real speech generation is blocked** until TopMediai's unspecified successful response and audio formats are verified. No live audio was generated or billed during creation. See [API status and completion steps](references/topmediai-api.md).

## Contents

- `SKILL.md`: Codex workflow and usage boundaries.
- `agents/openai.yaml`: display name and default prompt.
- `scripts/bulk_voice.py`: lesson validation, conservative drafts, lint findings, lossless chunks, manifests, WAV assembly, and resumable runner.
- `scripts/topmediai.py`: documented read-only API client, request builder, and explicit blocked synthesis adapter.
- `scripts/configure-key.ps1`: hidden session-only key prompt for PowerShell.
- `Voice Setup.vbs`: double-click Windows launcher with no terminal window.
- `scripts/voice_setup.py`: private key entry, connection check, and voice picker.
- `scripts/local_settings.py`: Windows-encrypted key storage and saved voice settings outside the project.
- `references/setup.md`: beginner account, key, and voice setup.
- `references/narration-cleanup.md`: contextual editing rules and examples.
- `references/topmediai-api.md`: verified facts, gaps, sources, limits, and costs.
- `examples/six-section-lesson.json`: complete reviewed sample, including a section longer than 500 characters.
- `tests/test_bulk_voice.py`: offline behavior tests using silent WAV fixtures, never real speech.
- `.gitignore`: local secrets, output, and caches.

## Use in Codex

Start with the [student guide](STUDENT-GUIDE.md) for a step-by-step walkthrough without commands. On first use, the skill instructs Codex to guide the student one step at a time, reuse existing setup, and explain the current audio-generation limitation before asking for account setup.

To install from GitHub, send this message to Codex:

```text
Use skill-installer to install https://github.com/AskAdelAcademy/bulk-voice-generation as bulk-voice-generation. The skill is at the repository root (path .).
```

The installer should use repository `AskAdelAcademy/bulk-voice-generation`, path `.`, and name `bulk-voice-generation`. The skill will be available on your next turn after successful installation. The Windows setup window opens on first use when configuration is missing. It does not open merely because files were installed.

**This is an unfinished preview for setup and preparation testing.** It does not generate speech yet. Do not buy credits solely to test this preview. The [integration status](references/topmediai-api.md) explains the remaining work.

Once installed, students can ask:

```text
Use $bulk-voice-generation on my attached six-section lesson. Prepare natural narration, help me choose a TopMediai voice, and save one audio file per section in a named output folder.
```

**Students do not need PowerShell, JSON, or File Explorer.** After installation, say **“Set up Bulk Voice Generation”** or request narration. The skill instructs Codex to check saved settings and open **Voice Setup** on Windows if the key or voice is missing. Paste the key into its hidden field, click **Check connection and save**, then choose a voice by name. Future lessons reuse these settings and skip setup. This runs on first use, not automatically during file installation; double-clicking `Voice Setup.vbs` is only a fallback when the host cannot launch it. See the [step-by-step setup guide](references/setup.md). The preview still cannot generate real speech.

Codex reads the entire lesson and creates normalized JSON. Required section fields: `title`, `transcript`; optional `number` preserves source numbering. Codex adds `narration_ready` and `cleanup_reviewed: true` after reviewing meaning and pronunciation. Array order controls filenames. Both transcripts are retained verbatim in the manifest. Raw CLI drafts are never automatically treated as reviewed narration.

## Try the six-section example now, without an API key

Students can simply ask Codex: **“Prepare the included six-section test lesson and show me the narration changes.”** No key is needed. The following commands are for Codex or an instructor performing technical checks.

In a terminal, change into this folder. Use Python 3.10+ (`py -3` on Windows if appropriate). No pip packages are required for the skill.

```powershell
python scripts/bulk_voice.py prepare examples/six-section-lesson.json --output outputs/six-section-review
python scripts/bulk_voice.py generate outputs/six-section-review --dry-run
python -m unittest discover -s tests -v
```

Inspect `outputs/six-section-review/manifest.json`: six sections, original and narration-ready text, filenames, voice, findings, chunk plans, and status. This creates **no audio**. Tests generate temporary silent WAV fixtures and clean them up. Use a fresh output folder on each prepare run; existing files are never overwritten by prepare.

## Once the live adapter has been completed and verified

Follow [setup](references/setup.md), run `check`, and list voices. Replace `SELECTED_SPEAKER_ID` and the name with a real entry; these are not credentials.

```powershell
python scripts/bulk_voice.py check
python scripts/bulk_voice.py voices --query English
python scripts/bulk_voice.py prepare examples/six-section-lesson.json --output outputs/six-section-audio --speaker SELECTED_SPEAKER_ID --voice-name "Selected voice"
python scripts/bulk_voice.py generate outputs/six-section-audio --dry-run
python scripts/bulk_voice.py generate outputs/six-section-audio
```

The last command is what Codex runs behind the scenes. Students request narration in plain language. At present it stops with a clear contract-verification message before any paid synthesis request. The framework targets six numbered WAV files, not MP3 files with the wrong encoding. Offer a short optional sample in a separate output folder when the adapter works.

To retry an explicitly rejected section after addressing the cause:

```powershell
python scripts/bulk_voice.py generate outputs/six-section-audio --section 2
```

Successful sections/chunks are reused. Interrupted or ambiguous requests are recorded as uncertain and require an explicitly authorized `--retry-uncertain`, because replay could charge twice. Do not run two generators on the same output folder simultaneously. Changing narration or voice requires a new prepared folder. Listen to all final sections, especially joins, before distributing them.

## Verification and limitations

Offline tests cover all six section outputs, chunk length and text preservation, assembled frame counts, title exclusion, unchanged-file resume, single-section retry, uncertain outcomes, transcript review, secret suppression, malformed audio, and the pre-network live-generation block. These are workflow tests, not proof of TopMediai voice quality or live availability. Account/voice endpoints were documentation-verified, not authenticated end-to-end tested. Current API gaps and plan requirements are recorded in the linked API reference.

Preview verification: all 20 offline tests passed, including encrypted storage, key reuse, search, pagination, save confirmation, and closing only after a successful save. The official Codex `quick_validate.py` passed after PyYAML was supplied in an ignored validation folder; the skill itself does not require PyYAML. The six-section example contains 1,325 narration characters split into seven chunks.

The Tkinter window was smoke-tested locally. Automated tests use synthetic credentials and silent audio fixtures. These checks do not establish live speech-generation support or successful installation on every student's computer. Real speech remains blocked as described above.
