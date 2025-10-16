# NPC Callout Spam Fix

## Problem Description

### Issue
Companions and NPCs were spamming callout messages about specific enemy NPCs even after combat had been avoided. The companion would continue sending messages to the same NPC repeatedly, even when the enemy was far away.

### Root Cause
The `is_valid_callout` function in `talker_trigger_callout.script` was missing two critical validation checks:

1. **No Distance Check**: Without a distance limit, NPCs could call out enemies that were extremely far away. After avoiding combat, the `on_enemy_eval` callback could still trigger for distant enemies, causing spam.

2. **Incomplete Target Validation**: The function checked if the spotter NPC was a living character but didn't verify the same for the target, potentially allowing callouts for dead or invalid targets.

## Solution

### Changes Made

#### 1. Added Distance Check
```lua
local MAX_CALLOUT_DISTANCE = 30  -- Distance in meters
```
A 30-meter distance limit ensures callouts only occur for enemies that are actually nearby and pose an immediate potential threat.

**Rationale for 30 meters:**
- Close enough to be relevant for imminent combat
- Far enough to give players/NPCs time to prepare
- Matches typical engagement ranges in S.T.A.L.K.E.R. Anomaly
- Prevents spam from distant enemies after combat avoidance

#### 2. Added Target Living Character Check
```lua
queries.is_living_character(target_obj)
```
This ensures both the spotter and the target are valid living characters before allowing a callout.

### Updated Validation Logic

The `is_valid_callout` function now validates all of the following conditions:

1. **Cooldown Period**: At least 30 seconds must have elapsed since the last callout (prevents spam)
2. **Spotter is Living**: The NPC making the callout must be alive
3. **Target is Living**: The enemy being called out must be alive
4. **Enemy Relationship**: The spotter and target must be enemies
5. **Not in Combat**: The spotter must not be currently in combat
6. **Within Range**: The target must be within 30 meters of the spotter

All conditions must be true for a callout to be valid.

## Code Changes

### File: `gamedata/scripts/talker_trigger_callout.script`

**Before:**
```lua
function is_valid_callout(npc_obj, target_obj)
    is_valid =
        (queries.get_game_time_ms() - last_callout_time_ms) > callout_cooldown_ms   and
        queries.is_living_character(npc_obj)                                        and
        queries.are_enemies(npc_obj, target_obj)                                    and
        not queries.is_in_combat(npc_obj)
    if is_valid then last_callout_time_ms = queries.get_game_time_ms() end
    return is_valid
end
```

**After:**
```lua
local MAX_CALLOUT_DISTANCE = 30

function is_valid_callout(npc_obj, target_obj)
    is_valid =
        (queries.get_game_time_ms() - last_callout_time_ms) > callout_cooldown_ms   and
        queries.is_living_character(npc_obj)                                        and
        queries.is_living_character(target_obj)                                     and
        queries.are_enemies(npc_obj, target_obj)                                    and
        not queries.is_in_combat(npc_obj)                                           and
        queries.get_distance_between(npc_obj, target_obj) <= MAX_CALLOUT_DISTANCE
    if is_valid then last_callout_time_ms = queries.get_game_time_ms() end
    return is_valid
end
```

### File: `tests/triggers/test_talker_trigger_callout.lua`

Added comprehensive test cases:
- `testCalloutWithinDistance`: Validates callouts work when target is within 30m
- `testCalloutBeyondDistance`: Validates callouts are blocked when target is beyond 30m
- `testCalloutTargetNotLiving`: Validates callouts are blocked when target is not living

## Impact

### Positive Effects
- **Eliminates Spam**: NPCs no longer spam callouts about distant enemies
- **More Realistic**: Callouts only occur for nearby, relevant threats
- **Better Performance**: Fewer unnecessary callout events reduce processing overhead
- **Improved Immersion**: Dialogue feels more natural and contextually appropriate

### No Negative Effects
- The 30-meter range is generous enough that legitimate callouts are not affected
- The fix only adds restrictions; it doesn't change the core callout behavior
- Existing callout functionality for nearby enemies remains unchanged

## Testing

The fix has been validated with test cases covering:
1. Normal callouts within range (should work)
2. Callouts beyond range (should be blocked)
3. Callouts with dead targets (should be blocked)

All tests pass successfully with the new validation logic.

## Configuration

The `MAX_CALLOUT_DISTANCE` constant can be adjusted if needed:
- **Lower values** (e.g., 20m): More restrictive, fewer callouts
- **Higher values** (e.g., 40m): More permissive, more callouts
- **Current value** (30m): Balanced for typical gameplay

To modify, edit the value in `gamedata/scripts/talker_trigger_callout.script`:
```lua
local MAX_CALLOUT_DISTANCE = 30  -- Change this value
```

## Credits

This fix was inspired by a user-reported issue and temporary fix. The solution has been refined and integrated with comprehensive documentation and testing.
