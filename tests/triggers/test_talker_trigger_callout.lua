package.path = package.path .. ';./bin/lua/?.lua;./bin/lua/*/?.lua'
local luaunit = require('tests.utils.luaunit')
local assert_or_record = require("tests.utils.assert_or_record")
package.path = package.path .. ';./gamedata/scripts/?.script'

----------------------------------------------------------------------------------------------------
-- Mocks
----------------------------------------------------------------------------------------------------

local interface = {
    register_game_event = function(unformatted_description, event_objects, witnesses)
        local event_data = {
            unformatted_description, event_objects, witnesses
        }
        assert_or_record('triggers', 'testTriggerReload', event_data)
    end
}

talker_game_queries = {}

function talker_game_queries.get_game_time_ms()
    return 0
end
function talker_game_queries.is_living_character(obj)
    return true
end
function talker_game_queries.is_in_combat(npc)
    return false
end
function talker_game_queries.are_enemies(npc, target)
    return true
end
function talker_game_queries.get_distance_between(obj1, obj2)
    return 20 -- Default distance within callout range (30m)
end

require('talker_trigger_callout')

----------------------------------------------------------------------------------------------------
-- Test callouts with different scenarios
----------------------------------------------------------------------------------------------------

function testTriggerCallout()
    on_enemy_eval()
end

function testCalloutWithinDistance()
    -- Mock objects
    local npc = {}
    local target = {}
    
    -- Set distance to be within range
    talker_game_queries.get_distance_between = function(obj1, obj2)
        return 25 -- Within 30m range
    end
    
    -- Should be valid
    local result = is_valid_callout(npc, target)
    luaunit.assertTrue(result, "Callout should be valid when target is within 30m")
end

function testCalloutBeyondDistance()
    -- Mock objects
    local npc = {}
    local target = {}
    
    -- Set distance to be beyond range
    talker_game_queries.get_distance_between = function(obj1, obj2)
        return 50 -- Beyond 30m range
    end
    
    -- Should not be valid
    local result = is_valid_callout(npc, target)
    luaunit.assertFalse(result, "Callout should be invalid when target is beyond 30m")
end

function testCalloutTargetNotLiving()
    -- Mock objects
    local npc = {}
    local target = {}
    
    -- Set distance within range
    talker_game_queries.get_distance_between = function(obj1, obj2)
        return 20
    end
    
    -- Make target not living
    local original_is_living = talker_game_queries.is_living_character
    talker_game_queries.is_living_character = function(obj)
        if obj == target then
            return false -- Target is dead
        end
        return true
    end
    
    -- Should not be valid
    local result = is_valid_callout(npc, target)
    luaunit.assertFalse(result, "Callout should be invalid when target is not living")
    
    -- Restore original function
    talker_game_queries.is_living_character = original_is_living
end

os.exit(luaunit.LuaUnit.run())