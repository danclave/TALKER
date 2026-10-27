package.path = package.path .. ";./bin/lua/?.lua;"
-- entities
local Event = require("domain.model.event")
local Character = require("domain.model.character")
local Item = require("domain.model.item")
local log = require('framework.logger')
local config = require('interface.config')

require('infra.STALKER.factions')
-- game interfaces
local query = talker_game_queries
local game_async = talker_game_async
local command = talker_game_commands

-- in the mod, IDs are always strings
local function get_id(obj)
    return tostring(query.get_id(obj))
end

local m = {}

------------------------------------------------------------
--- GET
------------------------------------------------------------

function m.get_characters_near(obj, distance)
    local nearby_character_objs = query.get_nearby_characters(obj, distance)
    return gameObj_to_characters(nearby_character_objs)
end

function m.get_characters_near_player(distance)
    local player_obj = query.get_player()
    return m.get_characters_near(player_obj, distance)
end

function m.get_companions()
    local companion_objs = query.get_companions()
    return gameObj_to_characters(companion_objs)
end

function m.get_player_character()
    local player_obj = query.get_player()
    return m.create_character(player_obj)
end

function m.get_name_by_id(game_id)
    local game_obj = query.get_obj_by_id(game_id)
    return query.get_name(game_obj)
end

------------------------------------------------------------
--- CONSTRUCTORS
------------------------------------------------------------

function gameObj_to_characters(gameObjs)
    local characters = {}
    for _, character in ipairs(gameObjs) do
        table.insert(characters, m.create_character(character))
    end
    return characters
end


function m.create_game_event(unformatted_description, involved_objects, witnesses)
    local game_time = query.get_game_time_ms()
    local world_context = query.describe_world()
    local new_event = Event.create_event(unformatted_description, involved_objects, game_time, world_context, witnesses)
    return new_event
end

-- AlifePlus integration: the squad's current A-Life objective as a phrase, or nil. Inert without AlifePlus.
local function get_alife_objective(obj)
    if not (ap_api and ap_api.get_record and ap_api.get_text) then return nil end
    local squad = query.get_squad(obj)
    if not squad then return nil end
    local record = ap_api.get_record({ squad_id = squad.id, assigned = true })
    if not record or not record.action_key then return nil end
    return ap_api.get_text(record.action_key)
end

function m.create_character(game_object_person)
    local game_id = get_id(game_object_person)
    local name = query.get_name(game_object_person)
    local experience = query.get_rank(game_object_person)
    local faction = get_faction_name(query.get_faction(game_object_person))
    local weapon = query.get_weapon(game_object_person)
    local weapon_description = nil
    if weapon then
        weapon_description = query.get_item_description(weapon)
    end
    local objective = get_alife_objective(game_object_person)
    log.spam('creating character with id: ' .. game_id .. ', name: ' .. name .. ', experience: ' .. experience .. ', faction: ' .. faction)
    return Character.new(game_id, name, experience, faction, weapon_description, objective)
end

function m.get_player_weapon()
    local player_obj = query.get_player()
    local weapon_obj = query.get_weapon(player_obj)
    local weapon = m.create_item(weapon_obj)
    return weapon
end

function m.create_item(game_object_item)
    local game_id = get_id(game_object_item)
    local name = query.get_item_description(game_object_item)
    return Item.new(game_id, name)
end

function m.create_dialogue_event(speaker_id, dialogue)
    log.debug('creating dialogue event')
    local speaker_obj = query.get_obj_by_id(speaker_id)
    local witnesses = m.get_characters_near(speaker_obj)
    local speaker_char = m.create_character(speaker_obj)
    local dialogue_event = m.create_game_event("%s said: %s", {speaker_char, dialogue}, witnesses)
    return dialogue_event
end

------------------------------------------------------------
--- OTHER
------------------------------------------------------------
-- ASYNCs
function m.repeat_until_true(seconds, func, ...)
    game_async.repeat_until_true(seconds, func, ...)
end

-- DIALOGUE
function m.display_dialogue(speaker_id, dialogue)
    log.debug('displaying dialogue')
    command.display_message(speaker_id, dialogue)
end

function m.display_error_to_player(message)
    command.display_hud_message(message, 3)
end

function m.display_to_player(message, seconds)
    if not config.SHOW_HUD_MESSAGES then
        return
    end
    seconds = seconds or 3
    command.display_hud_message(message, seconds)
end

function m.is_cooldown_over(LAST_GAME_TIME_MS, CD_MS)
    return (query.get_game_time_ms() - LAST_GAME_TIME_MS > CD_MS)
end

function m.get_distance(obj_id1, obj_id2)
    local obj1 = query.get_obj_by_id(obj_id1)
    local obj2 = query.get_obj_by_id(obj_id2)
    return query.get_distance_between(obj1, obj2)
end

function m.get_distance_to_player(obj_id)
    local obj = query.get_obj_by_id(obj_id)
    local player = query.get_player()
    return query.get_distance_between(obj, player)
end

-- to be moved
function m.is_player(character_id)
    return tostring(character_id) == "0"
end


local game_files = talker_game_files or require('tests.mocks.mock_game_queries') -- todo improve


-- I hotfixed this due to a loop dependency but it may also be possible that this function m.get_base_path() was just broken and requiring all of game_query
-- FILES
function m.get_base_path()
    return game_files.get_base_path()
end

local is_test_env, mock_game_adapter = pcall(require, 'tests.mocks.mock_game_adapter')
if false and is_test_env then
    return mock_game_adapter
end

function m.is_mock()
    return false
end

return m