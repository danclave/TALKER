-- interface.lua
local log = require("framework.logger")
local talker = require("app.talker")
local game_adapter = require("infra.game_adapter")

local m = {}

-- prototype

local function register_game_event(unformatted_description, event_objects, witnesses, important)
    log.info("Registering game event")
    local new_event = game_adapter.create_game_event(unformatted_description, event_objects, witnesses)
    log.debug("New event: %s", new_event)
    talker.register_event(new_event, important)
end

-- prevents issues later down the line with formatting
local function check_format_sanity(unformatted_description, ...)
    local additional_args = {...}
    local format_count = select(2, unformatted_description:gsub("%%s", ""))
    -- returns true if the amounts of variables like %s match the amount of arguments
    if (format_count > 0) and (format_count > #unpack(additional_args)) then
        log.error("Not enough arguments for description: %s", unformatted_description)
        return false
    end
    return true
end

function m.register_game_event(unformatted_description, event_objects, witnesses, important)
    if not check_format_sanity(unformatted_description, event_objects) then return end
    local success, error = pcall(register_game_event, unformatted_description, event_objects, witnesses, important)
    if not success then
        log.error("Failed to register game event: %s", error)
    end
end

return m
