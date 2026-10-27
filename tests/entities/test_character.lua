-- Requires
local luaunit = require('tests.utils.luaunit')
local assert_or_record = require("tests.utils.assert_or_record")

local Character = require('domain.model.Character')

-- Test Character creation
function testCharacterCreation()
    local char = Character.new("1", "John Doe", "Veteran", "Warrior")
    luaunit.assertEquals(char.game_id, "1")
    luaunit.assertEquals(char.name, "John Doe")
    luaunit.assertEquals(char.experience, "Veteran")
    luaunit.assertEquals(char.faction, "Warrior")
end

-- Test Character description method with dynamic personality incorporation
function testCharacterDescription()
    local char = Character.new(1, "John Doe", "Veteran", "Warrior")

    -- Get the description from the character object
    local description = Character.describe(char)

    -- Pattern to validate: must contain the character's name followed by some description with keywords
    local expected_pattern = "^John Doe, a .* Veteran Warrior$"

    -- Assert description matches the expected pattern
    luaunit.assertStrMatches(description, expected_pattern)
end

-- Test the AlifePlus objective is appended to the description when present
function testCharacterDescriptionWithObjective()
    local char = Character.new(1, "John Doe", "Veteran", "Warrior", "PKM", "Investigating a Massacre Site")

    local description = Character.describe(char)

    luaunit.assertStrContains(description, "who is currently Investigating a Massacre Site")
end

-- Test the description omits the objective clause when absent
function testCharacterDescriptionWithoutObjective()
    local char = Character.new(1, "John Doe", "Veteran", "Warrior")

    local description = Character.describe(char)

    luaunit.assertNotStrContains(description, "who is currently")
end

-- Run tests
os.exit(luaunit.LuaUnit.run())