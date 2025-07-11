-- dynamic_config.lua – values that depend on talker_mcm are now getters
local game_config = talker_mcm
local language = require("infra.language")

-- Changing it to local f = io.open("..\\openAi_API_KEY.key", "r") will use the open openAi_API_KEY.key in TALKER.
-- Without this change, people will get API_KEY = nil error in console.
local function load_api_key()
    -- Try TALKER-relative path
    local f = io.open("..\\openAi_API_KEY.key", "r")
    if f then return f:read("*a") end

    -- Try alternate filename
    f = io.open("..\\openai_api_key.txt", "r")
    if f then return f:read("*a") end

    -- Try Windows temp dir
    local temp_path = os.getenv("TEMP") or os.getenv("TMP")
    if temp_path then
        f = io.open(temp_path .. "\\openAi_API_KEY.key", "r")
        if f then return f:read("*a") end

        f = io.open(temp_path .. "\\openai_api_key.txt", "r")
        if f then return f:read("*a") end
    end

    -- Try env var
    local key = os.getenv("OPENAI_API_KEY")
    if not key or key == "" then
        error("Could not find OpenAI API key file or environment variable")
    end
    return key
end



-- helper
local function cfg(key, default)
    return (game_config and game_config.get and game_config.get(key)) or default
end

local c = {}

-- static values
c.EVENT_WITNESS_RANGE  = 25
c.NPC_SPEAK_DISTANCE   = 20
c.BASE_DIALOGUE_CHANCE = 0.25
c.player_speaks        = false
c.SHOW_HUD_MESSAGES    = true
c.OPENAI_API_KEY       = load_api_key()

local DEFAULT_LANGUAGE = language.any.long

-- dynamic getters
function c.language()
    return cfg("language", DEFAULT_LANGUAGE)
end

function c.language_short()
    return language.to_short(c.language())
end

function c.dialogue_model()
    return cfg("gpt_version", "gpt-4o")
end

function c.dialogue_prompt()
    return ("You are a dialogue generator for the harsh setting of STALKER. Swear if appropriate. " ..
            "Limit your reply to one sentence of dialogue. " ..
            "Write only dialogue without quotations or leading with the character name. Avoid cliche and corny dialogue " ..
            "Write dialogue that is realistic and appropriate for the tone of the STALKER setting. " ..
            "Don't be overly antagonistic if not provoked. " ..
            "Speak %s"
        ):format(c.language())
end

return c
