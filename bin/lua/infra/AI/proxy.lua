-- proxy.lua
local http   = require("infra.HTTP.HTTP")
local json   = require("infra.HTTP.json")
local log    = require("framework.logger")
local config = require("interface.config")
local inspect = require('framework.inspect')

local proxy = {}

-- model registry
local MODEL = {
  smart        = config.custom_dialogue_model(),
  mid          = config.custom_dialogue_model(),
  fast         = config.custom_dialogue_model_fast(),
  fine_dialog  = config.custom_dialogue_model(),
  fine_speaker = config.custom_dialogue_model(),
}

-- sampling presets
local PRESET = {
  creative = {temperature=0.9 ,top_p=1,frequency_penalty=0,presence_penalty=0},
  strict   = {temperature=0.0 ,top_p=1,frequency_penalty=0,presence_penalty=0},
}

-- helpers --------------------------------------------------------------
local API_URL = "http://127.0.0.1:8000/v1/chat/completions"
local API_MODELS_URL = "http://127.0.0.1:8000/v1/models"
local API_KEY = config.PROXY_API_KEY

local function build_body(messages, opts)
  opts = opts or PRESET.creative
  local reasoning_level = config.reasoning_level()

  local body = {
    model             = opts.model or MODEL.smart,
    messages          = messages,           -- plain Lua table
    temperature       = opts.temperature,
    top_p             = opts.top_p,
    max_tokens        = opts.max_tokens,
    frequency_penalty = opts.frequency_penalty,
    presence_penalty  = opts.presence_penalty,
  }

  if reasoning_level == -1 then
    body.thinking = {
      type = "enabled",
      budget_tokens = -1
    }
  else
    local reasoning_map = {
      [0] = "disable",
      [1] = "low",
      [2] = "medium",
      [3] = "high",
    }
    body.reasoning_effort = reasoning_map[reasoning_level]
  end

  return body
end



local function send(messages, cb, opts)
  assert(type(cb)=="function","callback required")

  local headers = {
    ["Content-Type"]  = "application/json",
    ["Authorization"] = "Bearer "..API_KEY,
  }

  local body_tbl = build_body(messages, opts)
  log.http("PROXY request: %s", json.encode(body_tbl)) -- encode only for log

  return http.send_async_request(API_URL, "POST", headers, body_tbl, function(resp, err)
    if resp and resp.error then
        err = resp.error
    end 
    if err or (resp and resp.error) then
      log.error("PROXY error: error:" .. json.encode(err or "no-err") .. " body:" .. json.encode(resp))
      error("PROXY error: error:" ..  json.encode(err or "no-err")  .. " body:" .. json.encode(resp))
    end
    local answer = resp.choices and resp.choices[1] and resp.choices[1].message
    log.debug("PROXY response: %s", answer and answer.content)
    cb(answer and answer.content)
  end)
end

local function get_model_list()
  local headers = {
    ["Content-Type"]  = "application/json",
    ["Authorization"] = "Bearer "..API_KEY,
  }

  local body_tbl = {}
  local requestId = http.send_request(API_MODELS_URL, "GET", headers, body_tbl)

  local response
  local error
  
  -- ugly 5s busy timeout
  local sec = tonumber(os.clock() + 5);
  while not response and not error and ( os.clock() < sec ) do
    log.info("waiting for models response");
      response, error = http.check_response(requestId)
  end

  log.info("models response " .. inspect(response))

  local resultPairs = {}
  if response and response.data then
    log.info("models list array result" .. inspect(response.data))
    for i, v in ipairs(response.data) do
      local pair = { v["id"], v["id"] }
      log.info("adding the pair: " .. inspect(pair))
      table.insert(resultPairs, pair)
    end
  elseif error then
    log.error("models error" .. inspect(error))
  else
    log.info("models probably timeout")
  end
  log.info("models final table", inspect(resultPairs))
  return resultPairs
end

-- public shortcuts -----------------------------------------------------
function proxy.generate_dialogue(msgs, cb)
  return send(msgs, cb, PRESET.creative)
end

function proxy.pick_speaker(msgs, cb)
  return send(msgs, cb, {model=MODEL.fast, temperature=0.0})
end

function proxy.summarize_story(msgs, cb)
  return send(msgs, cb, {model=MODEL.fast, temperature=0.2})
end

function proxy.get_model_list()
  return get_model_list()
end

return proxy
