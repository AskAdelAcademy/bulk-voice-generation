# TopMediai integration status

Checked against official documentation on 2026-10-08. This is a working preparation framework with documented read-only API integration, **not a verified live audio generator**.

| Verified contract | Source |
| --- | --- |
| API host `https://api.topmediai.com`; `x-api-key` header | [Official OpenAPI](https://api.topmediai.com/topmediai_api.json) |
| `POST /v1/text2speech`; JSON fields `text`, `speaker`, optional `emotion`; text length 1–500 | [TTS reference](https://docs.topmediai.com/api-reference/text-to-speech/text-to-speech) |
| `GET /v1/voices_list`; response `Voice` array with `speaker`, `name`, `Languagename` | [Voice reference](https://docs.topmediai.com/api-reference/text-to-speech/get-voice-list) |
| `GET /v1/get_api_key_info`; includes `key_words_counts`, `key_status`, and the secret key | [Account reference](https://docs.topmediai.com/api-reference/x-api-key-info/get-api-key-info) |

The TTS success response is declared as application/json with an empty schema. The official references reviewed do not establish a download URL field, audio encoding, polling contract, download URL expiry, idempotency, error-body schema, or key-status numeric meanings. The introductory TTS page exposed no additional contract. No audio response parser has been guessed. The web application's MP3/WAV export options do not establish the API's formats.

`TopMediai.synthesize_wav()` and `ensure_synthesis_ready()` deliberately stop before a billable request. The documented payload builder is implemented and tested. All production paths remain blocked until the missing contract is resolved. No override flag bypasses this block. The runner accepts normalized PCM WAV bytes from an adapter; a future verified adapter must decode/convert the actual API format into consistent PCM WAV before returning. Current intended section output is WAV; MP3 conversion requires a verified encoder and is not implemented. Never rename WAV bytes to MP3.

To finish the live adapter:

1. Obtain an official successful response example and supported formats, directly from updated documentation or TopMediai support. Record the source here. Do not ask for a user's key or an unredacted account response.
2. Implement exact response validation, success/error semantics, download or bounded polling, and decoding in `topmediai.py`. Allow only HTTPS public download destinations; never forward the API key to downloads or redirects. Bound network waits and download sizes.
3. Confirm whether a synthesis timeout can be reconciled without resubmission. Until then retain the uncertain-status behavior and no automatic POST retry.
4. Add response fixtures and tests for the verified contract, invalid audio, failures, timeouts, and expired URLs. Normalize all chunks to the same PCM format before joining.
5. With user-authorized credentials and a chosen voice, perform one short billed sample, listen to it, then a six-section run including a >500-character section and a resume check. Document results; only then remove the readiness block.

## Limits and costs

Split text into <=500-character requests without dropping words. The helper prefers punctuation/word boundaries and rejoins decoded PCM audio to one file per section. Chunk boundaries can affect prosody; listen to long sections. No section titles are added to payloads.

The [API purchase page](https://www.topmediai.com/api/text-to-speech-api/purchase/) lists character quotas and concurrency limits: Startup 200,000 / 5 concurrent; Growth 550,000 / 20; Scale 1,850,000 / 100; Business 8,000,000 / unlimited concurrency. This implementation is sequential. Verify current plan terms before purchase. Numeric prices were not exposed in the retrieved page, so no dollar quote is claimed. Exact request-per-minute limits and credit accounting were not confirmed.

The [API product page](https://www.topmediai.com/api/text-to-speech-api/) says API access is purchased separately from the web TTS subscription and advertises limited trial characters. Do not assume a particular free allowance. Check remaining credits and applicable license in the account. Samples and explicit retries can consume credits. Character totals are planning estimates, not a guaranteed invoice. The OpenAPI describes the service as experimental and subject to change.
