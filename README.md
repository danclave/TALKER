# TALKER
A LLM powered dialogue generator for STALKER Anomaly

![TALKER](images/talker.png)

## notes
You no longer require openAI api credits to be able to use this mod! Changing the LLM model is possible, I left a door open for it at least in the code if anyone wants to give it a shot.

This mod is provided free of charge with open code, practice your own due diligence and set spending limits on your account. I have tested for bugs that could cause large amounts of requests but that does not mean it's impossible!

## Table of Contents
- [How It Works](#how-it-works)
- [Installation Guide](#installation-guide)
- [The TALKER PDA (Voice App)](#the-talker-pda-voice-app)
- [Free Models Guide](#free-models-guide)
- [Using Local Models](#using-local-models)
- [Credits](#credits)

## How It Works
TALKER is more than a simple random phrase generator. It is a sophisticated, event-driven system that creates contextually relevant dialogue.

*   **Contextual Awareness:** The mod constantly monitors in-game events. When something noteworthy happens—a firefight erupts, a player reloads their weapon, an anomaly is triggered, or you simply speak to someone—TALKER registers it. This stream of recent events provides the context for the AI's dialogue generation.
*   **Unique Personalities:** Every NPC is treated as a unique character with a distinct profile, including their name, faction, experience level, and equipped weapon. Crucially, each character is assigned a **personality**, which dictates their tone, vocabulary, and general demeanor. This information is fed to the LLM, ensuring that a grizzled Duty veteran speaks differently from a rookie Loner.
*   **Intelligent Dialogue Triggers:** The mod uses a configurable system to determine when an NPC should speak, preventing a constant cacophony of chatter. This ensures that dialogue feels natural and impactful, occurring at moments of interest or in direct response to the player.

## Installation Guide
This guide will walk you through installing TALKER. For the best experience (especially with free API providers), using the recommended API key proxy is advised.

### Prerequisites

To get started, you'll need to download a few separate components.

**What to Download:**
1.  **The Mod Itself (Latest Source Code):** For the latest features and fixes, download the source code directly from the [**`main` branch**](https://github.com/danclave/TALKER/archive/refs/heads/main.zip).
2.  **Voice Utility Archive:** From the [TALKER Releases Page](https://github.com/danclave/TALKER/releases/latest), find the latest **MAIN** release and download the appropriate `TALKER-Mic-*.zip` archive for your operating system if you plan to use voice chat:
    - **Windows**: `TALKER-Mic-Windows-*.zip`
    - **Linux**: `TALKER-Mic-Linux-*.zip`
    - **macOS**: `TALKER-Mic-macOS-*.zip`
3.  **API Proxy:** Download the appropriate `LLM-API-Key-Proxy-*.zip` release for your operating system from its [own releases page](https://github.com/Mirrowel/LLM-API-Key-Proxy/releases/latest). This is highly recommended for connecting to AI services.

**Installation Steps:**

### Step 1: Install TALKER and Mic Utility
1.  It is recommended to use a mod manager like [Mod Organizer 2](https://lazystalker.blogspot.com/2020/11/mod-organizer-2-stalker-anomaly-setup.html).
2.  Install the TALKER source code zip you downloaded like any other Anomaly mod.
3.  If you plan to use voice chat, open the `TALKER-Mic-*.zip` archive you downloaded for your platform:
    - **Windows**: Extract `talker_mic.exe` into the mod's root folder (e.g., `E:\GAMMA\mods\TALKER`).
    - **Linux/macOS**: Extract `talker_mic` into the mod's root folder. You may need to make `talker_mic` executable (`chmod +x talker_mic`). But you are on linux, so figure it out.

### Step 2: Set Up Your AI Provider
You need to connect TALKER to an AI service. This is a one-time setup.

You have two options for connecting to an AI service:

**Option A: Use the Recommended API Proxy (For Stability & Flexibility)**

The [LLM-API-Key-Proxy](https://github.com/Mirrowel/LLM-API-Key-Proxy) is the best way to connect to AI services. It helps avoid rate-limits by rotating keys and natively supports many different providers (like Gemini, Anthropic, etc.), allowing you to switch between them easily. This is highly recommended, especially if you are using free services.

1.  **Download the Proxy**: Get the latest release from the [proxy's GitHub Releases page](https://github.com/Mirrowel/LLM-API-Key-Proxy/releases/latest).
2.  **Unzip It**: Extract the downloaded file to its own folder.
    **IMPORTANT (Mod Organizer 2 Users)**: You **must** place the proxy folder outside of your MO2 mods directory (e.g., do not put it in `E:\GAMMA\mods`). MO2's virtual file system will prevent the proxy from finding its configuration files. A safe location would be something like `C:\TALKER_Proxy` or a folder on your Desktop.
3.  **Configure and Run**: Simply run `proxy_app.exe` (without any arguments). This launches the new **interactive TUI (Text User Interface) launcher** with a powerful menu system:
    *   🚀 **Run Proxy**: Start the proxy server with your configured settings
    *   ⚙️ **Configure Proxy**: Set host, port, PROXY_API_KEY, and request logging
    *   🔑 **Manage Credentials**: Add/edit API keys and OAuth credentials
        - Supports any LiteLLM-compatible provider
        - OAuth support for Qwen Code and iFlow with automated browser authentication
        - Automatic discovery of existing credentials from environment variables and system directories
        - Export credentials for stateless deployment (Railway, Render, etc.)
    *   📊 **View Status**: See configured providers, credential counts, and advanced settings
    *   🔧 **Advanced Settings**: Configure custom OpenAI-compatible providers, model definitions, and concurrency limits
    
    The TUI automatically saves your settings to `launcher_config.json` and `.env` files.
    
    **After configuring credentials**, select **"Run Proxy"** from the main menu. A terminal window will appear, indicating the proxy is running. **Keep this window open while you play.**

**Option B: Direct API Key (Simpler, but less stable and limited)**

If you are using a paid service (OpenAI and Openrouter support only) and prefer a simpler setup, you can use your API key directly.

1.  Get your API key from your provider (e.g., [OpenAI](https://www.howtogeek.com/885918/how-to-get-an-openai-api-key/)).
2.  Create a file named `openai_api_key.txt` in the mod's root folder.
3.  Paste your API key into this file and save it.

### Step 3: Launch and Play
1.  If you are using the API Proxy (Option A), make sure `proxy_app.exe` is running.
2.  If you plan to use voice chat, run `talker_mic.exe` (Windows) or `./talker_mic` (Linux/macOS). The **TALKER PDA** opens - a mouse-enabled configuration interface styled after the in-game device. A short first-time wizard walks you through picking your language and transcription provider; from then on you land on the dashboard. See the full [TALKER PDA section](#the-talker-pda-voice-app) for everything it can do.
3.  Configure your provider, language and model in the PDA, optionally run a **Radio Check** to test your microphone, then press **GO LIVE**.
4.  Launch S.T.A.L.K.E.R. Anomaly.

### Step 4: Configure In-Game Settings (MCM)
Once in-game, you need to configure TALKER in the Mod Configuration Menu (MCM) before you can start talking to NPCs.

1.  **Open the MCM**: Open the MCM from the main menu.
2.  **Select AI Model Method**: Find the **"AI Model Method"** setting and select the option that matches your setup:
    *   **proxy**: If you are using the recommended API Proxy.
    *   **open-ai** or **open-router-ai**: If you are using a direct API key.
3.  **Set Your Custom Models (Proxy Users)**: If you are using the proxy, you can specify which models to use.
    *   **Custom AI Model**: Enter the full name of your primary model. 
        *   **Example**: `gemini/gemini-3.7-flash` for Gemini, `chutes/deepseek-ai/DeepSeek-V3` for Chutes, or `nvidia_nim/deepseek-ai/deepseek-r1` for Nvidia.
    *   **Custom AI Model Fast**: Enter the name of a smaller, faster, secondary model for less complex tasks.
        *   **Example**: `gemini/gemini-3.5-flash-lite`.

    **Important Note on Model Names (Provider Prefixes)**
    When using the proxy, you must include a **provider prefix** in the model name. This tells the proxy which service to send the request to. Think of it like an address for your AI model.

    The format is always `provider_name/model_name`.

    Here are the prefixes for some of the supported providers:
    *   **Gemini**: `gemini/` (e.g., `gemini/gemini-3.7-flash`)
    *   **Chutes**: `chutes/` (e.g., `chutes/deepseek-ai/DeepSeek-V3`)
    *   **Nvidia**: `nvidia_nim/` (e.g., `nvidia_nim/deepseek-ai/deepseek-r1`)

    You must use the full, correct name for the model to work. You can find a list of some of the available models and their full names in the [Free Models Guide](docs/Free_Models_Guide.md).
    Refer to the [LLM API Proxy documentation](https://github.com/Mirrowel/LLM-API-Key-Proxy) for more information.
4.  **Configure Reasoning Level**: This setting controls how much "thinking" a model does.
    *   **Auto**: The model decides the appropriate level of reasoning. **This is the recommended setting.**
    *   **None**: Disables reasoning entirely.
    *   **Low, Medium, High**: Manually sets the reasoning level. Higher levels can result in more detailed responses but will be slower.
5.  **Set Voice Provider (Proxy Users)**: To use the proxy for voice transcription, set the **"Voice Provider"** to **"gemini-proxy"**. (NOT IMPLEMENTED YET)

Now you're ready to play! You can talk to NPCs using two methods:
*   **Voice Chat**: Hold `Left Alt` to speak.
*   **Text Chat**: Press `Enter` to open a chat box and type.

**Note on local models & disk cache**: Local providers download their models once and cache them on disk, so subsequent starts work offline. Whisper models land in the Hugging Face cache (`~/.cache/huggingface/hub`), Vosk models in a `vosk_models/` folder next to the executable. The in-app **Model Manager** shows everything cached on disk with sizes and lets you delete what you no longer need.

---

## The TALKER PDA (Voice App)

`talker_mic.exe` is the voice half of TALKER: it records your voice when you hold the in-game talk key and transcribes it with the provider of your choice. Everything is configured in the **TALKER PDA** - a terminal interface styled after the in-game device. The mouse works everywhere, but every action also has a keyboard shortcut.

<!-- SCREENSHOT: PDA dashboard (Home screen with status cards + GO LIVE) -->

### Boot animation
Every launch greets you with a short animated boot screen - one of ten curated TALKER animations (CRT power-on, geiger ticks, matrix rain, cipher decrypt and friends), picked at random each time. Press **any key** to skip it.

<!-- SCREENSHOT: boot animation (pick a nice frame of one variant) -->

### First-run wizard
The first time you run the app, a small wizard walks you through the two decisions that matter: **the language you speak** and **who transcribes your voice**. `Esc` skips it; everything remains changeable later, and the wizard only ever appears when no settings file exists.

<!-- SCREENSHOT: first-run wizard, language step -->

### Choosing a provider
Four transcription providers are available:

| Provider | Needs | Notes |
|---|---|---|
| **Whisper local** (recommended) | nothing - fully offline after the model download | Best offline accuracy, 100 languages. `small` is the sweet spot and runs fine on any PC from the last decade; `base` is solid for English only; `tiny` is a last resort for very weak systems. English automatically uses the specialized `.en` variant of the chosen size. |
| **Gemini proxy** | the API proxy with Gemini API key(s) | Best quality overall; ordered fallback chain of lite models (3.5 -> 3.1). |
| **Custom models** (advanced) | the API proxy + credentials per provider | Your own fallback chain of *any* audio-capable model on your proxy, format `provider/modelname` (e.g. `gemini/gemini-3.5-flash-lite`, `openai/gpt-4o-audio-preview`). The model must support audio input. |
| **Vosk local** | nothing - fully offline | Ultra-light (~30-140 MB per language) fallback for weak systems; noticeably lower accuracy than Whisper on real microphone audio. |

<!-- SCREENSHOT: provider picker popup with detail panel -->

### Language
Always set explicitly - no auto-detection guessing games. The searchable list puts the usual suspects on top (English, British English, Russian, Ukrainian, Polish, Spanish), then all Whisper-supported languages alphabetically, then Vosk-only ones. Every entry shows what supports it (`whisper + vosk`, `whisper`, `vosk only`), and languages with several Vosk models (e.g. Russian) let you choose which one.

<!-- SCREENSHOT: language picker popup with search active -->

### Radio Check
The live test screen - and your best debugging tool. Press **Start** and speak:
*   **Live level meter** with the silence threshold marked on it: when your input stays left of the mark, the auto-stop countdown begins. Watch the countdown tick down - you can *see* exactly why recording stops (or why it never does).
*   The countdown only arms once you actually speak - silence before your first word never counts.
*   A big **REC** indicator while recording, and the transcription result lands in the **heard** panel with timing stats.
*   **Play last recording** replays what the mic captured (great for spotting a dead or muffled microphone).
*   Recent checks are kept in a short history so you can compare providers/languages side by side.

<!-- SCREENSHOT: radio check mid-recording, meter active + countdown -->

### Audio settings
Opened from Radio Check. This is where microphone problems get solved:
*   **Microphone picker** - all your input devices, applies immediately.
*   **Live input monitor** - the same meter as Radio Check, always on, so you can watch your level while you flip microphones or move the threshold.
*   **Silence threshold tuner** - how loud input must be to count as speech. The marker on the meter *is* the threshold; move it until your speech clearly crosses it.
*   **Mic gain** (0.5x - 4.0x) - a software volume booster for very quiet microphones. Applies to the recording itself; a red `CLIPPING` warning tells you to back it off.
*   **Hear yourself** - two modes, both off by default: *live echo* (hear yourself with a slight delay while tuning - use headphones, speakers feed back into the mic; turns itself off when the window closes) and *record & play* (every radio check plays your recording back).

<!-- SCREENSHOT: audio settings modal with live meter + threshold marker -->

### Model manager
Lists every model cached on disk (Vosk and Whisper) with sizes and disk locations, marks the ones currently in use, shows total disk usage, and deletes what you no longer need.

<!-- SCREENSHOT: model manager with a few cached models -->

### Power-user bits
*   **`F12`** - diagnostics pane (the app log, color-coded; opens itself on warnings).
*   **`F2`** - collapse the navigation sidebar to a thin rail.
*   **`F1`** - help. **`s`** save, **`q`** quit, `1-8` jump between screens, `/` focuses the language filter.
*   **GO LIVE** stashes your settings automatically; `talker_mic_settings.json` next to the exe holds everything.
*   **CLI bypass** for scripting: `talker_mic.exe whisper_local small`, `talker_mic.exe gemini_proxy gemini/gemini-3.5-flash-lite`, or `custom_proxy <provider/model>`.
*   Unsaved changes are marked with a `*` in the sidebar until you save.

<!-- SCREENSHOT: diagnostics pane open (F12) over any screen -->

---

## Free Models Guide
This mod is designed to be accessible to everyone, which is why it supports a variety of free AI models. This guide will help you get set up with free services so you can enjoy TALKER without any cost.

### Why Use the API Proxy?
The [LLM-API-Key-Proxy](https://github.com/Mirrowel/LLM-API-Key-Proxy) is the key to using free models effectively. Free services often have strict usage limits. The proxy helps you stay under these limits by rotating between multiple API keys. It also supports many different AI providers, giving you the flexibility to experiment and find the model that works best for you.

**Note**: Remember to run the proxy from its own folder, outside of any mod manager directories (like MO2), to ensure it works correctly.

### Getting Free API Keys
To use the recommended **Gemini via API Proxy** option in the launcher, you will need at least one Gemini API key. Here’s how to get one:

1.  **Google AI Studio**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey) to create a free API key.
2.  **Follow the Instructions**: The site will guide you through the process. It's quick and straightforward.
3.  **Add to Proxy**: Once you have your key, run `proxy_app.exe` to launch the interactive TUI, then select **"Manage Credentials"** to add it.

For a more detailed walkthrough and a list of other free providers, please refer to the full [Free Models Guide](docs/Free_Models_Guide.md).

**Note**: The proxy now features a modern **interactive TUI (Text User Interface)** launcher that makes configuration effortless. Run `proxy_app.exe` without arguments to access the full menu system for managing credentials, configuring settings, and running the proxy. The credential manager supports standard API keys and OAuth credentials, with automatic discovery from environment variables and system directories.

## Cheeki Breeki's video
  [![Cheeki Breeki](https://img.youtube.com/vi/WmM-PPKTA8s/0.jpg)](https://www.youtube.com/watch?v=WmM-PPKTA8s)

## Using Local Models

> ⚠️ **NOT RECOMMENDED** ⚠️
> 
> This option exists for advanced users who are already experienced with local AI hosting.
> **If you don't already know how to run and evaluate local models, do not use this option.**
> 
> TALKER is designed for large cloud-hosted models (100B+ parameters). Local models that run 
> on consumer hardware are typically 3-32B parameters—significantly smaller and less capable. 
> This causes real problems:
> 
> 1. **Poor instruction following** — TALKER requires models that reliably follow specific 
>    formats (e.g., "respond with only the speaker's ID"). Smaller models often fail at this, 
>    returning incorrect formats that break the mod's functionality entirely.
> 2. **Nonsensical or generic dialogue** — Small models lack the capacity to understand world 
>    context, character personalities, and STALKER-specific details. Expect responses that are 
>    off-topic, repetitive, or completely unaware of the situation.
> 
> ### No Support Provided
> 
> **TALKER does not provide support for local AI models or their hosting.** If you choose this 
> path, you are on your own. Issues with Ollama, model quality, performance, or "the dialogue 
> isn't good" are outside the scope of this mod's support.

### Setup
1. Install [Ollama](https://ollama.ai/)
2. `ollama pull llama3.2` and `ollama pull llama3.2:1b`
3. `ollama serve`
4. In-game, select "Local" in MCM

## credits
Many thanks to
- [balls of pure diamond](https://www.youtube.com/@BallsOfPureDiamond), for making cool youtube videos and helping me brainstorm, playtest and stay hyped
- ThorsDecree for helping playtest
- [Cheeki Breeki](https://www.youtube.com/@CheekiBreekiTv)
- the many extremely helpful modders in the Anomaly discord
- Tosox
- RavenAscendant
- NLTP_ASHES
- Thial
- Lucy
- xcvb
- momopate
- Darkasleif
- Mirrowel
- Encrypterr
- lethrington
- Dunc
- Demonized
- Majorowsky
- beemanbp03
- abbihors, for boldly going where no stalker mod has gone before
- (Buckwheat in Russian) helping investigate pollnet
- many more who I rudely forgot
