# Beginner setup

## Students: no commands on Windows

After the skill is installed, attach or paste your lesson into Codex and say:

> Use Bulk Voice Generation for this lesson. Help me set up my voice.

Codex handles the scripts and lesson preparation. For first-time setup:

1. Codex checks your saved settings and opens **Voice Setup** for you if a key or voice is missing. You do not need to find a file or run commands.
2. Click **Open TopMediai to get my key**, then create an account or sign in.
3. If **Click Activate** does not work, the API page shows **Unknown creator**, or your key does not appear, try logging out from that API page and signing in again from the **same page** with your usual login method. Then try **Click Activate** again. This resolved the issue in our setup test; it is a troubleshooting option, not a required step for everyone.
4. If the key row shows **Click Activate**, click it. Copy the displayed API key and paste it into the setup window's hidden field.
5. Click **Check connection and save**.
6. Click **Find voices**, choose a **Language / accent** from the dropdown, and type part of a voice name to narrow results instantly. Clear the initial **English** search when choosing another language. Results appear 50 at a time; **Next 50**, **Previous 50**, and **Clear filters** help you browse. Select a voice and click **Save voice**.
7. A **Voice saved** message confirms that your choice was saved. You can use **Save voice and close** to finish in one action. The setup window does not need to stay open for Codex to use saved settings. Return to Codex and say **My voice is set up**.

For later lessons, attach the lesson and ask Codex to make narration using your saved voice. You do not need to handle filenames, JSON, commands, or voice IDs.

The window opens when you first ask Codex to set up or use the skill, rather than merely when its files are installed. You can also say **“Set up Bulk Voice Generation”** immediately after installation. If setup is already complete, Codex reuses it and skips the window. If your computer prevents Codex from opening it, double-clicking `Voice Setup.vbs` is a fallback.

**Preview limitation:** setup can check the account and save a voice. Real narration and listening samples are not available until the TopMediai audio integration is completed. You can ask Codex to prepare the six-section example without an account or key.

The launcher needs an available Python with Tkinter; it tries the Windows Python launcher and the known bundled Codex runtime location. No installation or download is performed. If Windows blocks VBS or the window does not appear, ask Codex to launch `scripts/voice_setup.py` directly using an available Python. The runtime path is not guaranteed on every Codex installation. This graphical setup currently supports Windows only.

## How the saved key is protected

The window stores an encrypted key in `%LOCALAPPDATA%\BulkVoiceGeneration\api-key.dpapi`, outside the skill and lesson folders. It uses Windows DPAPI in current-user scope, with no plaintext fallback. Other programs running as your Windows user may still access it; use your own Windows account on shared computers. See [Microsoft's DPAPI documentation](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata).

The voice name, language, and ID are saved separately in `voice.json` in the same local settings folder; this file contains no key. Codex reads saved settings automatically on its next helper call. **Forget saved key** removes this helper's saved copy; it does not revoke the key at TopMediai or remove an independently configured environment variable. Existing environment keys take precedence and are reused without asking the student to type them again.

The remaining instructions are optional technical alternatives for instructors and non-Windows systems. Students using the setup window can stop here.

## Get a key

1. Open the official [TopMediai TTS API page](https://www.topmediai.com/api/text-to-speech-api/).
2. Create an account or log in. Choose **Get API Key** and find the API key in the account/profile area. Button names may change.
3. If the API page does not recognize your account (for example, **Unknown creator**), log out and sign in again from that same API page using the same login method. If **Click Activate** is shown, activate the trial key. If access still fails, use the contact form or official support. The [documentation](https://docs.topmediai.com/) links to API services and support.
4. Check your API credits/plan. The website's ordinary TTS subscription is separate from API access.
5. Copy the key privately. It is like a password that lets the skill use your TopMediai allowance. Never paste it into Codex chat, lesson files, examples, repositories, screenshots, or public support requests.

## Store it locally

As an alternative to the Windows setup window, use the environment variable `TOPMEDIAI_API_KEY`. The scripts reuse it and do not accept a command-line key argument. No key is bundled, saved in lesson JSON, or written to a manifest. `.gitignore` excludes common secret files and output folders but cannot protect files already tracked by Git.

On Windows, open your own PowerShell terminal and run:

```powershell
. .\scripts\configure-key.ps1
```

The hidden prompt sets the variable for that terminal session only, keeping the key out of command history and disk. Run the Python commands in the same terminal. Existing variables are reused. To make the key available to a running Codex app, it must be configured in the environment from which the app starts; a child terminal cannot update an already-running parent app.

For persistent Windows setup, search Start for **Edit environment variables for your account**, create a user variable named `TOPMEDIAI_API_KEY`, enter the key in its value field, and restart Codex/terminals. A persistent environment variable is stored by Windows and is **not encrypted credential-vault storage**; processes under your account may read it. For a shared computer prefer a session variable or an OS credential manager that injects the variable at launch. Do not put it in a shell profile or `.env` committed to Git.

On macOS/Linux with Bash, use a private terminal session:

```bash
read -r -s -p 'TopMediai API key: ' TOPMEDIAI_API_KEY
export TOPMEDIAI_API_KEY
printf '\n'
```

After running commands, close the terminal to discard a session-only key. If exposed, revoke/rotate it in TopMediai; deleting a local copy is insufficient.

## Verify and choose a voice

Python 3.10+ is required; there are no third-party Python runtime packages. On Windows `py -3` can replace `python` if installed.

```sh
python scripts/bulk_voice.py check
python scripts/bulk_voice.py voices --query English
```

The check calls the documented account endpoint and prints only status and remaining count. Numeric status meanings are not documented; the helper does not label a number “active.” Generation must ultimately be confirmed by a short real sample. Voice listing prints names, languages, and speaker IDs. Use a listed ID in `prepare --speaker ... --voice-name ...`. Add `--emotion ...` only for a voice confirmed to support that emotion. A missing key gives friendly setup guidance; API errors never dump raw responses.

Live speech and test-sample synthesis are blocked pending the response contract described in [integration status](topmediai-api.md). No purchase or key is needed for offline preparation/tests.
