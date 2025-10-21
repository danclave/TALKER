# TALKER
A LLM powered dialogue generator for STALKER Anomaly

> [!WARNING]
> | ⚠️ **DEVELOPMENT BUILD - HERE BE DRAGONS** ⚠️ |
> |:----------------------------------------:|
> This build is a **Work-In-Progress (WIP)** and is **always experimental and highly unstable**. It contains features that are under active development, may be feature-incomplete, contain severe bugs, or have features that will be completely removed without warning.
>
> **Expect crashes, data loss, and unexpected behavior.**
>
> ---
>
> **For a stable release, please use the [`main` branch](https://github.com/danclave/TALKER/tree/main).** The `dev` branch is intended for testing and contributions.


![TALKER](images/talker.png)

## notes
You no longer require openAI api credits to be able to use this mod! Changing the LLM model is possible, I left a door open for it at least in the code if anyone wants to give it a shot.

This mod is provided free of charge with open code, practice your own due diligence and set spending limits on your account. I have tested for bugs that could cause large amounts of requests but that does not mean it's impossible!

## Installation Guide
This guide will walk you through installing TALKER. For the best experience (especially with free API providers), using the recommended API key proxy is advised.

### Prerequisites

To get started, you'll need to download a few separate components.

**What to Download:**
1.  **The Mod Itself (Latest Source Code):** For the latest features and fixes, download the source code directly from the [**`dev` branch**](https://github.com/danclave/TALKER/archive/refs/heads/dev.zip).
2.  **Voice Utility Archive:** From the [TALKER Releases Page](https://github.com/danclave/TALKER/releases/latest), find the latest release and download the `TALKER-Mic-*.zip` archive if you plan to use voice chat.
3.  **API Proxy:** Download the `LLM-API-Key-Proxy` release from its [own releases page](https://github.com/Mirrowel/LLM-API-Key-Proxy/releases/latest). This is highly recommended for connecting to AI services.

**Installation Steps:**

### Step 1: Install TALKER and Mic Utility
1.  It is recommended to use a mod manager like [Mod Organizer 2](https://lazystalker.blogspot.com/2020/11/mod-organizer-2-stalker-anomaly-setup.html).
2.  Install the TALKER source code zip you downloaded like any other Anomaly mod.
3.  If you plan to use voice chat, open the `TALKER-Mic-*.zip` archive you downloaded. Extract its contents (`talker_mic.exe` and `launch_mic.bat`) into the mod's root folder (e.g., `E:\GAMMA\mods\TALKER`).

### Step 2: Set Up Your AI Provider
You need to connect TALKER to an AI service. This is a one-time setup.

You have two options for connecting to an AI service:

**Option A: Use the Recommended API Proxy (For Stability & Flexibility)**

The [LLM-API-Key-Proxy](https://github.com/Mirrowel/LLM-API-Key-Proxy) is the best way to connect to AI services. It helps avoid rate-limits by rotating keys and natively supports many different providers (like Gemini, Anthropic, etc.), allowing you to switch between them easily. This is highly recommended, especially if you are using free services.

1.  **Download the Proxy**: Get the latest release from the [proxy's GitHub Releases page](https://github.com/Mirrowel/LLM-API-Key-Proxy/releases/latest).
2.  **Unzip It**: Extract the downloaded file to its own folder.
    **IMPORTANT (Mod Organizer 2 Users)**: You **must** place the proxy folder outside of your MO2 mods directory (e.g., do not put it in `E:\GAMMA\mods`). MO2's virtual file system will prevent the proxy from finding its configuration files. A safe location would be something like `C:\TALKER_Proxy` or a folder on your Desktop.
3.  **Add API Keys**: Run `setup_env.bat`. A window will pop up to help you add your API keys.
4.  **Start the Proxy**: Double-click `proxy_app.exe`. A terminal window will appear, indicating the proxy is running. **Keep this window open while you play.**

**Option B: Direct API Key (Simpler, but less stable and limited)**

If you are using a paid service (OpenAI and Openrouter support only) and prefer a simpler setup, you can use your API key directly.

1.  Get your API key from your provider (e.g., [OpenAI](https://www.howtogeek.com/885918/how-to-get-an-openai-api-key/)).
2.  Create a file named `openai_api_key.txt` in the mod's root folder.
3.  Paste your API key into this file and save it.

### Step 3: Launch and Play
1.  If you are using the API Proxy (Option A), make sure `proxy_app.exe` is running.
2.  If you plan to use voice chat, run `launch_mic.bat` and select your preferred transcription service.
3.  Launch S.T.A.L.K.E.R. Anomaly.

### Step 4: Configure In-Game Settings (MCM)
Once in-game, you need to configure TALKER in the Mod Configuration Menu (MCM) before you can start talking to NPCs.

1.  **Open the MCM**: Open the MCM from the main menu.
2.  **Select AI Model Method**: Find the **"AI Model Method"** setting and select the option that matches your setup:
    *   **proxy**: If you are using the recommended API Proxy.
    *   **open-ai** or **open-router-ai**: If you are using a direct API key.
3.  **Set Your Custom Models (Proxy Users)**: If you are using the proxy, you can specify which models to use.
    *   **Custom AI Model**: Enter the full name of your primary model. 
        *   **Example**: `gemini/gemini-2.5-flash` for Gemini, `chutes/deepseek-ai/DeepSeek-V3` for Chutes, or `nvidia_nim/deepseek-ai/deepseek-r1` for Nvidia.
    *   **Custom AI Model Fast**: Enter the name of a smaller, faster, secondary model for less complex tasks.
        *   **Example**: `gemini/gemini-2.5-flash-lite-preview-06-17`.

    **Important Note on Model Names (Provider Prefixes)**
    When using the proxy, you must include a **provider prefix** in the model name. This tells the proxy which service to send the request to. Think of it like an address for your AI model.

    The format is always `provider_name/model_name`.

    Here are the prefixes for some of the supported providers:
    *   **Gemini**: `gemini/` (e.g., `gemini/gemini-2.5-flash`)
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

**Note on API Keys & `launch_mic.bat`**: If you chose the Direct API Key and don't want to create the `.key` file manually, you can run `launch_mic.bat` once. It will ask for your key and save it for you. After this one-time setup, you only need to run the launcher when you want to use voice chat.

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
3.  **Add to Proxy**: Once you have your key, use the `setup_env.bat` script from the proxy to add it.

For a more detailed walkthrough and a list of other free providers, please refer to the full [Free Models Guide](docs/Free_Models_Guide.md).

## Cheeki Breekivideo
- [![Cheeki Breeki](https://img.youtube.com/vi/WmM-PPKTA8s/0.jpg)](https://www.youtube.com/watch?v=WmM-PPKTA8s)

## using local models
1. install ollama
2. ollama pull llama3.2
3. ollama pull llama3.2:1b
4. ollama serve
5. run game and pick local models

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
