# Free Models Guide

This guide provides a detailed walkthrough for setting up and using free AI models with TALKER. The best way to use free models is with the [LLM-API-Key-Proxy](https://github.com/Mirrowel/LLM-API-Key-Proxy), which helps you avoid rate limits and manage multiple API keys.

---

## Important Updates (December 2025)

*   **Gemini Free Tier Gutted**: Google has drastically reduced Gemini API rate limits, making standard API keys essentially **unusable** for TALKER. Gemini 2.5 Pro has been **removed from the free tier entirely**. Flash and Flash-Lite are now limited to **20 requests per day** (down from 250-1,000). This is nowhere near enough for normal gameplay.
*   **New Recommendations**: **Nvidia** is now the recommended free provider, with **iFlow** as an excellent alternative. Both offer generous limits and access to high-quality models.
*   **Gemini CLI Still Works**: If you specifically want Gemini models, the **Gemini CLI (OAuth)** method still provides higher rate limits and remains viable.

---

## Important Updates (September 2025)

*   **New Nvidia Models Added**: Several new models from Nvidia have been added to the guide, including `kimi-k2-instruct-0905` (recommended), `qwen3-next-80b-a3b-instruct` (recommended), `mistral-small-24b-instruct`, `deepseek-v3.1`, and various other versions of `qwen`.
*   **Model Reorganization**: The Nvidia model list has been reorganized into "Non-Thinking," "Thinking," and "Problematic" categories to help users better select models for their needs.
*   **Nvidia Performance Note**: A note has been added to the Nvidia section to inform users that model availability and performance can vary based on server load.

## Important Updates (July 2025)

*   **Chutes is No Longer Free**: Chutes has moved to a paid model(one-time, like openrouter). While this is a significant change, new free alternatives are being actively investigated and will be added to this guide as they become available.
*   **Community Impact**: The transition of Chutes to a paid service has unfortunately led to some users, particularly those generating NSFW content, migrating and abusing other free platforms. This has put a strain on those services, and their stability may be affected. Please use all services responsibly. Yes, blame Gooners. They killed Chutes for everyone and now they are killing the rest of the free services too(one already confirmed heavily impacted, with over 10x in usage).

---

### A Note on Thinking Models

"Thinking" models are designed for complex reasoning, which means they are often **considerably slower** than their non-thinking counterparts. For general use in the mod, **non-thinking models are usually the better choice** for a more responsive experience.

## Supported Free Providers
1.  **Nvidia (Recommended)**: Nvidia offers a robust selection of high-quality models with generous rate limits. Their Mistral, Kimi and DeepSeek models are excellent performers for TALKER.
2.  **iFlow (Recommended - OAuth)**: A powerful aggregator platform providing free access to multiple premium models (Qwen, DeepSeek, GLM, Kimi) through OAuth 2.0 authentication. Supports both OAuth and direct API keys. Very reliable.
3.  **Gemini CLI (Advanced - OAuth)**: An advanced provider using OAuth 2.0 to access Google's internal Gemini CLI API endpoints with significantly higher rate limits than standard API keys. Requires OAuth setup but provides access to high-quality Gemini models.
4.  **Mistral (Preliminary)**: Mistral.ai offers a free tier with seemingly very decent usage limits. This provider is currently being investigated for full integration with TALKER, but early adopters can add their API keys to the proxy and experiment with models like Mistral Small, Mistral Large, and Mixtral reasoning models.
5.  **Gemini (API Keys)**: ⚠️ **No longer recommended.** Google has slashed free tier limits to ~20 requests/day, making this essentially unusable for normal gameplay. Use Nvidia, iFlow, or Gemini CLI instead.

---

## 1. Gemini (API Keys)

> ⚠️ **WARNING** ⚠️
> 
> As of December 2025, Google has gutted the Gemini free tier rate limits to the point of being **unusable for TALKER**. 

---

### Archived Information (For Reference Only)

The information below is kept for historical reference but the rate limits and recommendations 
are no longer accurate.

---

Google's Gemini is the top choice for its generous free tier and strong performance. By creating multiple projects, you can generate several API keys (up to 12 per account in our experience), which dramatically increases your free usage limits when used with the API proxy. Do note that it is recommended to use multiple accounts instead of maxing out projects - I don't have concrete evidence, but multiple users had their projects "banned" for some reason, and they were unable to create new projects or API keys. So multiple accounts with 2-4 keys each is more than enough.

### Models and Rate Limits

Gemini and Gemma models offer a range of options, each with different trade-offs between speed, intelligence, and rate limits.

**Gemini Models**

| Model Name (Provider Prefix)                     | Speed      | Intelligence | Notes                                                                                                                                                               |
| ------------------------------------------------ | ---------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `gemini/gemini-2.5-pro`                          | Slowest    | Smartest     | The most powerful model, ideal for complex dialogue and reasoning. Even as the "slowest" Gemini model, it's still faster than most non-Gemini models.                  |
| `gemini/gemini-2.5-flash`                        | Fast       | Smart        | **Recommended for most tasks.** A great balance of speed and intelligence, making it a versatile choice for both general use and thinking mode.                       |
| `gemini/gemini-2.5-flash-lite`     | Fastest    | Decent       | The quickest model, perfect for fast-paced interactions where raw speed is the top priority.                                                                        |

**Gemma Models**

| Model Name (Provider Prefix)       | Speed      | Intelligence | Notes                                                                                                                                                               |
| ---------------------------------- | ---------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `gemini/gemma-3-27b-it`            | Fast       | Good         | A strong performer that cannot reason. With enough keys, its high rate limit allows for virtually unlimited use, making it a great fallback option for non-reasoning tasks. |

**Free Tier Rate Limits (Per key)**

| Model                                    | RPM | TPM     | RPD    |
| ---------------------------------------- | --- | ------- | ------ |
| Gemini 2.5 Pro                           | 5   | 125,000 | 50    |
| Gemini 2.5 Flash                         | 10  | 250,000 | 250    |
| Gemini 2.5 Flash-Lite Preview 06-17      | 15  | 250,000 | 1,000  |
| Gemma 3 & 3n                               | 30  | 15,000  | 14,400 |

*   **RPM**: Requests Per Minute
*   **TPM**: Tokens Per Minute
*   **RPD**: Requests Per Day

### How to Get Multiple Gemini API Keys

Follow these steps to get the maximum number of free keys from a single Google account:

**Step 1: Open the Google Cloud Console**
*   Navigate to the [Google Cloud Console](https://console.cloud.google.com/). If you aren't logged in, you'll be prompted to do so.

**Step 2: Open the Project Picker**
*   In the top-left corner of the dashboard, you'll see a project name (e.g., "My First Project"). Click on it to open the project selection window.

**Step 3: Create Multiple Projects**
*   In the project selection window, click the **"New Project"** button.
*   Give the project any name you like (e.g., "TALKER-Key-1"). The name isn't important as you won't see it again.
*   Repeat this process until Google Cloud no longer allows you to create new projects (usually around 12).

**Step 4: Generate an API Key for Each Project**
**WARNING**: It is strongly recommended **not** to use your main Google account for creating API keys. There have been reports of accounts being affected, though the exact reasons are unclear. To be safe, create a separate, dedicated Google account for generating API keys.

*   Now, go to the [Google AI Studio API Key Page](https://aistudio.google.com/app/apikey).
*   Click the **"Create API key"** button.
*   A dropdown menu will appear. Select one of the projects you just created.
*   An API key will be generated. **Copy this key immediately.**

**Step 5: Add Keys to the Proxy**
*   Run `proxy_app.exe` (without any arguments) from the LLM-API-Key-Proxy folder to launch the interactive TUI.
*   Select **"Manage Credentials"** from the main menu.
*   Choose **"Add API Key"** and select **Gemini** as the provider.
*   Paste in the first Gemini API key you copied and confirm.
*   The tool will ask if you want to add another key. Repeat this process for each key you generated.
*   When finished, the tool will automatically save all keys to your `.env` file.

**Step 6: Repeat for All Projects**
*   Go back to the Google AI Studio page and repeat step 4 for all your projects, adding each new key to the proxy as you go. You can add all your keys in a single session of the TUI credential manager.

**Step 7: Profit!**
*   You now have a pool of Gemini API keys. The proxy will automatically rotate through them, giving you a much higher free usage limit. You can even do this with multiple Google accounts for virtually unlimited use.

---


## 2. Nvidia

Nvidia offers a wide selection of high-quality models, making it a powerful option for experimentation. However, there are a few key limitations to keep in mind.

**Account and API Key Limitations**
*   You can only create one API key per Nvidia account.
*   Creating a new account requires phone number verification, which makes it difficult to acquire multiple keys.

**A Note on Rate Limits**
*   Nvidia's rate limits are not officially published. They appear to be generous and dependent on server load, but it's always best to use the service reasonably.

**A Note on Model Availability and Speed**
*   The availability and speed of Nvidia's models can vary significantly based on server load. A model that is unresponsive or very slow one day may be very fast the next. It's a good idea to have backup models in mind or test their speeds (in progress).

### How to Get an Nvidia API Key

**Step 1: Create and Verify Your Account**
*   Go to [build.nvidia.com](https://build.nvidia.com/) and create a new account or log in to an existing one.
*   You will need to verify your account with a phone number and email address to proceed.

**Step 2: Generate Your API Key**
*   Once you are logged in, navigate to the main dashboard.
*   Click the **"Get API Key"** button to generate your unique key.

**Step 3: Add the Key to the Proxy**
*   Run `proxy_app.exe` (without any arguments) from the LLM-API-Key-Proxy folder to launch the interactive TUI.
*   Select **"Manage Credentials"** from the main menu.
*   Choose **"Add API Key"** and select **Nvidia NIM** as the provider.
*   Paste in your Nvidia API key and confirm.

### Available Models

Here are some of the notable models available through Nvidia's API:

**Non-Thinking Models**

| Model Name (Provider Prefix)                               | Notes                                                                                                |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `nvidia_nim/moonshotai/kimi-k2-instruct`                   | **Recommended.** One of the best models for storytelling and writing. Decently fast and reliable.     |
| `nvidia_nim/moonshotai/kimi-k2-instruct-0905`              | **Recommended.** A versioned variant of kimi-k2-instruct, as excellent for storytelling and writing, but usually slower or even unavailable.    |
| `nvidia_nim/qwen/qwen3-next-80b-a3b-instruct`              | **Recommended.** Non-thinking instruct version of Qwen, perfect for this use case - fast and almost always available.  |
| `nvidia_nim/meta/llama-4-maverick-17b-128e-instruct`       | A very fast model. Quality can vary and is very censored. But it is always available at high speed. It is sometimes too literal at what it does. Borders on unusable. |
| `nvidia_nim/google/gemma-3-27b-it`                         | A powerful, but small, model from Google that is a great alternative to other options. Faster then mistral.   |
| `nvidia_nim/mistralai/mistral-small-24b-instruct`          | Usually too slow, but can be used for instruct tasks when speed is not critical. A very good storytelling model. |


---
**Thinking Models** - Note that thinking models are often significantly slower than non-thinking models. For general use in the mod, non-thinking models are usually the better choice for a more responsive experience.

> [!WARNING]
> **DeepSeek Models on Nvidia**: All DeepSeek models hosted on Nvidia suffer from being randomly unavailable or slow, with no way to predict when these issues will occur. Because of this unpredictability, **DeepSeek models cannot be recommended** for consistent use on Nvidia's platform.

| Model Name (Provider Prefix)                               | Notes                                                                                                                                      |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `nvidia_nim/deepseek-ai/deepseek-r1-0528`                  | The latest and most powerful version of DeepSeek-R1, excellent for reasoning tasks. Too slow with reasoning and commonly unavailable.                                     |
| `nvidia_nim/deepseek-ai/deepseek-r1`                       | The base version of DeepSeek-R1, a solid all-arounder. Faster, compared to 0528. Still not recommended   |
| `nvidia_nim/qwen/qwen3-next-80b-a3b-thinking`              | **Recommended.** A powerful and fast thinking model. Usually fast enough with reasoning—only recommended thinking model here.   |
| `nvidia_nim/bytedance/seed-oss-36b-instruct`               | Interesting small thinking model that is, sadly, not very fast.  |

---

***Problematic Models***

*At the time of writing, the following models were very problematic to run (unavailable or very slow) and may be unstable:*

| Model Name (Provider Prefix)                               | Notes                                                                                                                                      |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `nvidia_nim/qwen/qwen3-235b-a22b`                          | A very large model from the Qwen family, capable of high-quality output but may be slower. (Thinking model by default in the mod)             |
| `nvidia_nim/deepseek-ai/deepseek-v3.1`                     | Hybrid reasoning model that will reason if thinking is set to **high**. Suffers from availability issues like other DeepSeek models.   |
| `nvidia_nim/deepseek-ai/deepseek-v3.1-terminus`            | Hybrid reasoning model that will reason if thinking is set to **high**. Suffers from availability issues like other DeepSeek models.   |

---


## 3. Mistral (Preliminary)

Mistral.ai offers a free tier with seemingly very decent usage limits. This provider is currently being investigated for full integration with TALKER. In the meantime, you can add your Mistral API key yourself by following the proxy guide and experiment with it.

### How to Get a Mistral API Key

**Step 1: Create an Account**
*   Go to [mistral.ai](https://mistral.ai/) and create a new account or log in.

**Step 2: Generate Your API Key**
*   Navigate to the API section in your dashboard.
*   Click **"Create API Key"** and copy the generated key.

**Step 3: Add the Key to the Proxy**
*   Run `proxy_app.exe` (without any arguments) from the LLM-API-Key-Proxy folder to launch the interactive TUI.
*   Select **"Manage Credentials"** from the main menu.
*   Choose **"Add API Key"** and select **Mistral** from the provider list.
*   Paste in your Mistral API key and confirm.

### Models and Notes
*   Models: To be added once fully investigated. Popular options include Mistral Small and Mistral Large, or Mixtral reasoning models, which show promise for both general and reasoning tasks.
*   Rate Limits: Free tier appears generous, but exact limits are under review.

For now, this allows early adopters to test Mistral's capabilities directly.

---

## 4. Gemini CLI (Advanced - OAuth)

Gemini CLI is an advanced provider that uses OAuth 2.0 authentication to access Google's internal Gemini API endpoints—the same ones used by the Google Cloud Code extension. This provides access to significantly higher rate limits compared to the standard free Gemini API keys.

### Key Advantages

*   **Higher Rate Limits**: Access to internal Google Cloud endpoints (`cloudcode-pa.googleapis.com`) offers much more generous limits than the public API.
*   **Free Tier Access**: Works with Google Cloud's free tier—no credit card required for initial setup.
*   **Same Models as Regular Gemini**: Access to the same high-quality Gemini models (Pro, Flash, Flash-Lite).
*   **Automatic Project Discovery**: The proxy automatically finds or creates a Google Cloud Project for you.
*   **Smart Fallback System**: Automatically switches to preview/alternate models when rate limits are hit(When available).

### Important Considerations

*   **Easier Than API Keys**: OAuth setup is actually *simpler* than manual API key generation—just 2 button clicks in the TUI and you're done!
*   **Google Account Required**: You'll need a Google account to authenticate.
*   **Slightly Higher Latency**: Gemini CLI has slightly higher latency (more "laggy") than direct API access, but this is only very noticeable when using the Pro model. Flash and Flash-Lite models are still very responsive.
*   **Potential Account Risk**: While unlikely, using unofficial API endpoints may carry some risk to your Google account. Use a secondary account if concerned.

### How to Set Up Gemini CLI

**Step 1: Run the Credential Manager**
*   Launch `proxy_app.exe` (without any arguments) from the LLM-API-Key-Proxy folder to open the interactive TUI.
*   Select **"Manage Credentials"** from the main menu.
*   Choose **"Add OAuth Credential"** and select **"Gemini CLI"** from the provider list.

**Step 2: Complete OAuth Flow**
*   Your browser will automatically open to Google's login page.
*   Sign in with your Google account (use a secondary account if concerned about risk).
*   Grant the requested permissions when prompted.
*   The proxy will automatically handle the OAuth callback and save your credentials.

**Step 3: Automatic Configuration**
*   The proxy will automatically:
    *   Discover your Google Cloud Project ID (or help you create a free-tier project).
    *   Validate your credentials.
    *   Save everything to `oauth_creds/gemini_cli_oauth_1.json`.

**Step 4: Token Refresh**
*   Gemini CLI credentials are automatically refreshed in the background **while the proxy is running**.
*   If the proxy is closed for multiple days, you may need to re-authenticate when you restart it.
*   If a refresh token expires, the proxy will guide you through re-authentication.

### Available Models

| Model Name (Provider Prefix)                     | Speed      | Intelligence | Notes                                                                                                                                                               |
| ------------------------------------------------ | ---------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `gemini_cli/gemini-2.5-pro`                      | Slowest    | Smartest     | The most powerful model, ideal for complex dialogue and reasoning. Access to high-limit internal endpoints makes this much faster than the public API version.    |
| `gemini_cli/gemini-2.5-flash`                    | Fast       | Smart        | **Recommended for most tasks.** Excellent balance of speed and intelligence with high rate limits.                                                                |
| `gemini_cli/gemini-2.5-flash-lite`               | Fastest    | Decent       | The quickest option with the highest rate limits. Perfect for fast-paced interactions.                                                                             |

### Rate Limits

Gemini CLI uses Google's internal Cloud Code API endpoints, which have significantly higher limits than the public API:

*   **Estimated Limits**: Much higher than standard Gemini API (exact limits vary by project tier and usage patterns).
*   **Tier Detection**: The proxy automatically detects your Google Cloud tier (free-tier, legacy-tier, or paid Gemini Advanced).

> [!WARNING]
> **Mixed Tier Warning**: If you load both free-tier and paid Gemini Advanced credentials simultaneously, you may experience unexpected behavior with model availability and rate limits. It's recommended to use consistent tier credentials.

### Technical Details

*   **Authentication**: Full OAuth 2.0 web flow with automatic token refresh every 10 minutes (configurable via `OAUTH_REFRESH_INTERVAL`).
*   **Invalid Grant Handling**: If refresh tokens expire due to inactivity, the proxy automatically triggers re-authentication.

---

## 5. iFlow (Advanced - OAuth)

iFlow is a powerful aggregator platform that provides free access to multiple high-quality models through a unified API. It uses OAuth 2.0 authentication with a local callback server to manage credentials securely.

### Key Advantages

*   **Multiple Premium Models**: Access to Qwen, DeepSeek, GLM, Kimi, and other top-tier models through a single provider.
*   **Free Usage**: Generous free tier with access to the latest models.
*   **Active Development**: Frequently adds new models and features.
*   **Dual Authentication**: Supports both OAuth and direct API keys for flexibility.

### Important Considerations

*   **Easier Than API Keys**: OAuth setup is actually *simpler* than manual registration and API key generation—just 2 button clicks in the TUI and you're done!
*   **Chinese Platform**: iFlow is a Chinese service, but does not require a Chinese phone number for registration. Use your google account to register during the OAuth flow.
*   **Technical Note**: The OAuth flow runs a temporary local callback server on port 11451 and uses a hybrid approach (OAuth tokens fetch your API key automatically).
*   **Availability**: Being a free aggregator, model availability and stability may vary based on server load. Though generally reliable.

### How to Set Up iFlow OAuth

**Step 1: Run the Credential Manager**
*   Launch `proxy_app.exe` (without any arguments) from the LLM-API-Key-Proxy folder to open the interactive TUI.
*   Select **"Manage Credentials"** from the main menu.
*   Choose **"Add OAuth Credential"** and select **"iFlow"** from the provider list.

**Step 2: Complete OAuth Flow**
*   The proxy will start a temporary local server on port 11451 to handle the OAuth callback.
*   Your browser will automatically open to iFlow's login page.
*   Authorize the application to access your account.
*   You'll be automatically redirected back to a success page.

**Step 3: Automatic Configuration**
*   The proxy will automatically:
    *   Exchange the authorization code for OAuth tokens.
    *   Fetch your iFlow API key from your user profile.
    *   Save everything to `oauth_creds/iflow_oauth_1.json`.

**Step 4: Token Refresh**
*   iFlow credentials are automatically refreshed in the background **while the proxy is running** (tokens are refreshed 24 hours before expiry).
*   If the proxy is closed for multiple days, you may need to re-authenticate when you restart it.
*   If a refresh token expires, the proxy will guide you through re-authentication.

### Alternative: Direct API Key

If you prefer not to use OAuth, you can also use iFlow with a standard API key:

1. Log in to [iFlow](https://iflow.cn) and navigate to your [API settings](https://platform.iflow.cn/en/profile?tab=apiKey).
2. Generate an API key from your dashboard.
3. In the proxy TUI, select **"Add API Key"** instead of **"Add OAuth Credential"**.
4. Choose **"iFlow"** and paste your API key.

> [!NOTE]
> **API Key Expiration**: iFlow API keys only work for a limited time (the exact duration is stated on the page when you create the key). You'll need to regenerate and update your key periodically. OAuth credentials are recommended for automatic renewal.

### Available Models

iFlow provides access to a wide variety of models from different providers. Here are some of the notable models:

| Model Name (Provider Prefix)                     | Type              | Notes                                                                                                                                      |
| ------------------------------------------------ | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `iflow/kimi-k2`                                  | General           | **Recommended.** Kimi's latest model, strong for storytelling and creative writing.                                                                         |
| `iflow/kimi-k2-0905`                             | General           | **Recommended.** Versioned variant of Kimi K2.                                                                                                              |
| `iflow/deepseek-v3.2`                            | General           | **Recommended.** Latest DeepSeek model with strong reasoning capabilities.                                                                                 |
| `iflow/deepseek-v3.1`                            | Hybrid Reasoning  | **Recommended.** Hybrid model that will reason when thinking is enabled.                                                                                    |
| `iflow/deepseek-r1`                              | Reasoning         | **Read note on thinking models in other sections** DeepSeek's dedicated reasoning model (slower but smarter).                                                                                 |
| `iflow/glm-4.6`                                  | General           | GLM's latest general-purpose model.                                                                                                        |
| `iflow/qwen3-max`                                | General           | **Recommended.** Qwen's most powerful general model.                                                                                                        |
| `iflow/qwen3-235b-a22b-instruct`                 | Instruct          | **Recommended.** One of Qwen's largest instruction-following models.                                                                                        |
| `iflow/qwen3-235b-a22b-thinking-2507`            | Reasoning         | **Read note on thinking models in other sections** Qwen's large-scale thinking/reasoning model.                                                                                               |

### Rate Limits

*   **Free Tier**: iFlow offers generous free usage, but exact limits are not publicly documented and may vary by user/region.
*   **Fair Use**: The service operates on a fair use basis. Excessive usage may result in temporary throttling.
*   **Automatic Refresh**: OAuth tokens are refreshed automatically 24 hours before expiry to prevent service interruptions.

### Troubleshooting

*   **Port 11451 Already in Use**: If another application is using port 11451, close it or modify the `CALLBACK_PORT` in the proxy source code.
*   **Token Expired**: If you see authentication errors, the proxy will automatically attempt to refresh your token. If that fails, it will guide you through re-authentication.

---
