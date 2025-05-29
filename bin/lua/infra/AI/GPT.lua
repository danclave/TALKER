local gpt = {}

-- Dependencies
package.path = package.path .. ";./bin/lua/?.lua;"
local http_module = require("infra.HTTP.HTTP")
local logger = require("framework.logger")
local json = require("infra.HTTP.json")
local file_io = require("infra.file_io")
local config = require("interface.config")

-- Constants
gpt.model_smart = "gpt-4-turbo"
gpt.model_mid = "gpt-4o"
gpt.model_fast = "gpt-4o-mini"
gpt.model_fine_tuned_dialogue = "ft:gpt-4o-2024-08-06:personal::A721Jmn6"
gpt.model_fine_tuned_pick_speaker = "ft:gpt-4o-mini-2024-07-18:personal::A9ndhQlH"

-- TODO allow tweaking by the user
-- Configuration
gpt.config_determinist = {
    temperature = 0.0,
    top_p = 1.0,
    max_tokens = 150,
    frequency_penalty = 0.0,
    presence_penalty = 0.0
}

gpt.config_creative = {
    temperature = 0.9,
    top_p = 1.0,
    max_tokens = 150,
    frequency_penalty = 0.0,
    presence_penalty = 0.0
}

-- Private variables
local api_key

-- Helper functions
local function load_api_key()
    api_key = config.OPENAI_API_KEY
end

local function construct_request_body(messages, config, model)
    config = config or gpt.config_creative
    model = model or gpt.model_smart

    local converted_messages = {}
    for i, msg in ipairs(messages) do
        if type(msg) == "table" and msg.content then
            converted_messages[i] = {
                role = msg.role,
                content = json.convert_to_utf8(msg.content:gsub('"', "'"))
            }
        elseif msg.content then
            converted_messages[i] = msg
            converted_messages[i].content = json.convert_to_utf8(converted_messages[i].content)
        end
    end

    return {
        model = model,
        messages = converted_messages,
        temperature = config.temperature,
        top_p = config.top_p,
        max_tokens = config.max_tokens,
        frequency_penalty = config.frequency_penalty,
        presence_penalty = config.presence_penalty
    }
end

function save_training_data(messages, response_message)
    -- convert to a json string and append to a jsonl file
    local file = "training_data/unsorted_training_data.jsonl"
    local combined_messages = {}
    for _, message in ipairs(messages) do
        table.insert(combined_messages, message)
    end
    table.insert(combined_messages, response_message)
    file_io.write(file, json.encode(combined_messages) .. "\n")
end

-- Core functionality
function gpt.send_request(messages, callback, config, model)
    if not api_key then load_api_key() end

    -- configure the request
    local POST = "POST"
    local url = "https://api.openai.com/v1/chat/completions"
    local headers = {
        ["Content-Type"] = "application/json",
        ["Authorization"] = "Bearer " .. api_key
    }
    -- construct the request body
    local body = construct_request_body(messages, config, model)
    logger.http("Sending request: %s",  body.messages)
    

    -- Send the request, then call the callback with the response for the sake of async
    return http_module.send_async_request(url, POST, headers, body, function(response, errorResponse, request_id)
        if errorResponse or response.error then
            local message = "Error in GPT request: " .. (response.error.message)
            logger.error(message)
            -- throw an error
            error(message)
            return true
        else
            local response_message = response.choices[1].message
            -- save_training_data(messages, response_message)
            local content = response_message.content
            logger.http("Received response:",content)
            callback(content)
        end
    end)
end

-- Interface
function gpt.summarize_story(messages, callback)
    return gpt.send_request(messages, callback, gpt.config_determinist, gpt.model_fast)
end

function gpt.pick_speaker(messages, callback)
    return gpt.send_request(messages, callback, gpt.config_determinist, gpt.model_fast)
end

function gpt.generate_dialogue(messages, callback)
    return gpt.send_request(messages, callback, gpt.config_creative, gpt.model_smart)
end

return gpt