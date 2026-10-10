# Your first lesson with Bulk Voice Generation

You can use ordinary messages in Codex. You do not need PowerShell, programming, or special file formats.

Codex can prepare your lesson, connect your TopMediai account, and generate one WAV narration file per section. Local preparation needs no API credits. Real narration and samples use your TopMediai credits.

## 1. Start after installation

Send this message in Codex:

> Use $bulk-voice-generation. Help me get started, one step at a time.

Codex will check whether setup is already complete. If you only want to try lesson preparation, say:

> Prepare the included six-section example and show me the narration changes.

## 2. Connect your account, if you want to set it up now

On Windows, Codex opens the private **Voice Setup** window for you when needed.

1. Click **Open TopMediai to get my key**.
2. Sign in or create an account on TopMediai, then find **Get API Key**.
3. If **Click Activate** does not work, the API page shows **Unknown creator**, or your key does not appear, try **Log out** from that API page, then sign in again from the **same page** using your usual login method (for example, Google sign-in). Then try **Click Activate** again. This resolved the issue in our setup test; it may help if the page has an outdated login session.
4. If the key row shows **Click Activate**, click it to activate the trial key.
5. Copy the key. It lets this skill access your TopMediai account allowance, so treat it like a password.
6. Paste it into the setup window's hidden key field, never into the Codex conversation.
7. Click **Check connection and save**.

If a key is already configured, leave the field blank to reuse it. If anything goes wrong, tell Codex the error message without sharing the key. There is no need to purchase credits merely to try local lesson preparation. TopMediai account access and credits are separate from your Codex subscription.

The setup window saves the key encrypted for your Windows account, outside lesson files. It currently supports Windows only. If the window does not appear, tell Codex so it can check the launch; you do not need to troubleshoot commands yourself.

## 3. Choose your voice

1. Click **Find voices** once to load the available voices.
2. Choose a **Language / accent** from the dropdown, then type part of a voice name in the search field. Results narrow as you type; multiple search words can match both the name and language. Clear the initial **English** text when looking for another language.
3. Select a matching voice. The list shows up to 50 results at a time; use **Next 50** or narrow your search further. **Clear filters** starts over, and **Refresh voice list** reloads available voices.
4. Click **Save voice** to save and keep browsing, or **Save voice and close** to finish setup. A **Voice saved** message confirms success; click **OK**. If saving fails, the window stays open so you can resolve it.
5. The setup window does not need to stay open during lesson preparation or narration. Close it if it is still open, then tell Codex:

> My voice is set up. What is the next step?

Codex verifies the saved settings. You will not need to repeat this for every lesson. Ask Codex for a short listening sample after saving your voice.

## 4. Give Codex your lesson

Attach a lesson file that Codex can read, or paste the lesson into the conversation. Include the sections in order, with a title and narration for each. For example:

```text
Section 1: Getting started
Narration: Welcome. In this lesson, we will learn how to observe details carefully.

Section 2: Your materials
Narration: Bring a notebook, a pencil, and a familiar object.
```

Then say:

> Prepare this lesson for narration using my saved voice. Keep one file per section and put the results in a folder called My First Lesson.

Codex reads the whole lesson, keeps the section order, and prepares natural spoken text. Titles are not read aloud unless they are part of the narration. The original text is kept alongside the narration-ready version.

## 5. Review the prepared lesson

Codex will show you where the prepared files were saved and describe meaningful narration changes. You can say:

> Show me how you changed links and abbreviations before narrating.

Or:

> Keep that technical term exactly as written, and explain how it will be pronounced.

Preparation does not create audio yet. When the text is ready, continue to the voice sample or full narration.

## 6. Generate and listen

To check the voice first, say:

> Make a short voice sample from the first section.

Listen to the sample. Then say:

> That voice works. Generate the complete lesson.

Codex will save one numbered audio file per section and a manifest recording the text, voice, filenames, and results. Samples and full narration use TopMediai credits. If a section fails, ask Codex to retry that section; it preserves completed files and explains any retry that might incur a duplicate charge.

## Your next lesson

Attach or paste the next lesson and say:

> Use $bulk-voice-generation for this lesson with my saved voice.

To change your voice, say **“Help me choose a different voice.”** To reopen setup, say **“Open Voice Setup.”** Your key always belongs in the private setup window, not the conversation.
