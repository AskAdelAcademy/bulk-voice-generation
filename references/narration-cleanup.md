# Contextual narration cleanup

Two stages are intentional: a conservative Python draft and a contextual Codex edit. Python normalizes line endings and whitespace and flags awkward content without deleting educational material. Codex reads the complete lesson, edits each narration, and compares it against its original before marking it reviewed. Retain both versions in JSON and the output manifest.

Use minimal changes. Do not shorten explanations, omit examples, change facts, or turn bullets into a summary. Speak every meaningful bullet as a sentence or a naturally separated item. Preserve pauses through punctuation. Remove Markdown emphasis delimiters without altering the emphasized words; preserve mathematical operators instead of globally deleting symbols. Expand an abbreviation only when its intended pronunciation is clear. Use the lesson's language; do not apply English pronunciation to every subject or language.

Examples of context-dependent edits:

| Written | Spoken |
| --- | --- |
| Visit https://www.example.com/download to download the program. | Visit the download link provided with this lesson to download the program. |
| Click [Download Codex](https://example.com/download). | Click the Codex download link provided with this lesson. |
| **Keep your notes.** | Keep your notes. |
| The API returns JSON. | The A P I returns JAY-suhn. |
| The URL begins with https://. | The U R L begins with H T T P S, colon, slash, slash. |

The pronunciation example is a draft choice, not a universal substitution; test the selected voice. Do not invent a supplied lesson link if none exists: retain the original link in the written lesson and refer to it there, or ask where learners can access it.

Do not automatically strip HTML, code, parentheses, file paths, URLs, or visual instructions. In a web-design lesson, HTML tags may be the learning objective. In a computing lesson, explain a path in speech. Preserve important parenthetical definitions as clauses. For a chart instruction, retain its comparison or conclusion instead of merely deleting “look at the chart.” If a visual is unavailable and needed for meaning, ask for its content.

For prepared JSON, preserve `transcript`, edit `narration_ready`, and set `cleanup_reviewed: true`. Re-run prepare into a new output folder. The lint findings are advisory even after review, since technical narration may legitimately retain symbols. Review means the flagged content was considered in context, not that every flag must disappear.
