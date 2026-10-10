# TopMediai integration

The official [TTS reference](https://docs.topmediai.com/api-reference/text-to-speech/text-to-speech) documents POST https://api.topmediai.com/v1/text2speech, the x-api-key header, and JSON fields text, speaker, optional emotion. Text length is 1–500 characters. GET /v1/voices_list lists voices; GET /v1/get_api_key_info checks the account. Account responses contain the key itself, so the helper returns only selected numeric fields.

## Response verified by a live test

On 2026-10-09 an authorized short request using the saved Red-Glasses voice returned HTTP 200 JSON with numeric status: 200, a message string, and data containing type, name, speaker, and oss_url. The URL used HTTPS on files.topmediai.com. No polling was required. These are observations from the official service, whose OpenAPI still does not define the success body. Other response variants remain unsupported.

The download had a .wav URL and audio/x-wav header but an ID3/MP3 payload. The helper therefore uses FFmpeg to decode content and normalize chunks to 24 kHz, mono, 16-bit PCM WAV. It assembles one output WAV per section. MP3 export is not implemented.

Downloads never carry the API key, permit only HTTPS files.topmediai.com on port 443, reject credentials in URLs, do not follow redirects, and enforce time/size limits. Unknown responses or download failures are uncertain and may have consumed credits. No synthesis POST is retried automatically. Known HTTP 400/401/403/422/429 rejections are recorded separately. No idempotency or timeout-reconciliation API was confirmed.

## Decoder and testing

See [setup](setup.md). FFmpeg is checked before paid synthesis. A system FFmpeg, installed imageio-ffmpeg, or Windows per-user runtime is supported. No binary or secret is bundled in GitHub. Tests use synthetic credentials and response fixtures; production calls use the saved user-selected voice.

## Limits and costs

Split text losslessly into <=500-character requests; processing is sequential. Samples and explicit retries consume credits. Titles are excluded unless part of narration. Listen at chunk boundaries because prosody can vary.

The [API purchase page](https://www.topmediai.com/api/text-to-speech-api/purchase/) lists plan-dependent quotas and concurrency. API access is separate from the web TTS subscription. No dollar price is guaranteed here. This test account initially reported 5,000 characters; that is not a universal trial allowance. The official API is experimental and may change.
