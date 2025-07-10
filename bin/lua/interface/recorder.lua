-- recorder.lua
-- this module is responsible for the logic needed to record the player's dialogue.
-- it interacts with the microphone module which handles more pure microphone related logic

-- function recorder.to get the names of nearby characters
package.path = package.path .. ";./bin/lua/?.lua"
local logger = require('framework.logger')
local game_adapter = require('infra.game_adapter')
local prompt_builder = require('infra.AI.prompt_builder')
local mic = require('infra.mic.microphone')
local json = require("infra.HTTP.json")

local recorder = {}

local function get_names_of_nearby_characters()
    logger.info("get_names_of_nearby_characters")
    local nearby_characters = game_adapter.get_characters_near_player()
    local names = {}
    for _, character in ipairs(nearby_characters) do
        table.insert(names, character.name)
    end
    return names
end

-- function recorder.to record the player's dialogue
function recorder.start(callback)
    logger.info("Listening for player dialogue...")
    mic.stop()
    mic.clear_transcription()
    -- Get names of nearby characters to enhance transcription accuracy
    local names = get_names_of_nearby_characters()
    local prompt = prompt_builder.create_transcription_prompt(names)

    mic.start(prompt)

    -- Asynchronously check for the transcription result
    game_adapter.repeat_until_true(0.1, function()
        if not mic.is_mic_on() then return true end -- stop looping
        game_adapter.display_to_player(mic.get_status(), 0.1)
        local dialogue = mic.get_transcription()

        mic.clear_transcription()
        if not dialogue then return false end -- continue looping
        dialogue = json.utf8_to_codepage(dialogue)
        mic.stop()
        if callback then
            callback(dialogue)
        end
        return true  -- stop looping
    end)
end

return recorder