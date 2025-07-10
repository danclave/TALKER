local log = require("framework.logger")

local c = talker_game_commands

local m = {}

function m.talker_player_speaks(dialogue)
    log.debug("Calling trigger talker_player_speaks with arg: %s", dialogue)
    c.SendScriptCallback("talker_player_speaks", dialogue)
end

function m.talker_game_event(unformatted_description, event_objects, witnesses, important)
    log.debug("Calling trigger talker_game_event with args: %s, %s, %s, %s", unformatted_description, event_objects, witnesses, important)
    c.SendScriptCallback("talker_game_event", unformatted_description, event_objects, witnesses, important)
end

function m.talker_game_event_near_player(unformatted_description, involved_objects, important)
    log.debug("Calling trigger talker_game_event_near_player with args: %s, %s, %s", unformatted_description, involved_objects, important)
    c.SendScriptCallback("talker_game_event_near_player", unformatted_description, involved_objects, important)
end

return m
