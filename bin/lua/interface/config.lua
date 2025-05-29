local game_config = talker_mcm

local function load_api_key()
    local file = io.open("openAi_API_KEY.key", "r")
    if file then return file:read("*a") end
    -- else try env variable
    local key = os.getenv("OPENAI_API_KEY")
    if key == "" then
        error("Could not find OpenAI API key file")
    end
    return key
end

local c = {}

-- 25 mystery units
c.EVENT_WITNESS_RANGE = 25
c.NPC_SPEAK_DISTANCE = 20
-- 25% chance
c.BASE_DIALOGUE_CHANCE = 0.25
-- does the player character speak automatically?
c.player_speaks = false
-- prompt
c.DIALOGUE_PROMPT = "You are a dialogue generator for the harsh setting of STALKER. Swear if appropriate. Limit your reply to one sentence of dialogue. Write only dialogue without quotations or leading with the character name. Avoid cliche and corny dialogue that is too aware of the popular aspects of the setting. Write dialogue that is realistic and appropriate for the tone of the STALKER setting. Don't be overly antagonistic if not provoked. Speak Ukrainian."

-- model for writing dialogue
c.DIALOGUE_GPT_MODEL = game_config and game_config.get("gpt_version") or "gpt-4o"
c.SHOW_HUD_MESSAGES = true
c.OPENAI_API_KEY=load_api_key()

return c
