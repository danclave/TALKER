--
-- json.lua
--
-- Copyright (c) 2020 rxi
--
-- Permission is hereby granted, free of charge, to any person obtaining a copy of
-- this software and associated documentation files (the "Software"), to deal in
-- the Software without restriction, including without limitation the rights to
-- use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
-- of the Software, and to permit persons to whom the Software is furnished to do
-- so, subject to the following conditions:
--
-- The above copyright notice and this permission notice shall be included in all
-- copies or substantial portions of the Software.
--
-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
-- IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
-- FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
-- AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
-- LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
-- OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
-- SOFTWARE.
--

-- This version was slightly modified by Dan to better work with STALKER Anomaly

-------------------------------------------------------------------------------
-- CYRILIFIER
---------------------------------------------------------------------------------------------------------------------------------------------------
local CP1251 = { -- CYRILLIC
    [0x0402] = 0x80,  -- CYRILLIC CAPITAL LETTER DJE
    [0x0403] = 0x81,  -- CYRILLIC CAPITAL LETTER GJE
    [0x201A] = 0x82,  -- SINGLE LOW-9 QUOTATION MARK
    [0x0453] = 0x83,  -- CYRILLIC SMALL LETTER GJE
    [0x201E] = 0x84,  -- DOUBLE LOW-9 QUOTATION MARK
    [0x2026] = 0x85,  -- HORIZONTAL ELLIPSIS
    [0x2020] = 0x86,  -- DAGGER
    [0x2021] = 0x87,  -- DOUBLE DAGGER
    [0x20AC] = 0x88,  -- EURO SIGN
    [0x2030] = 0x89,  -- PER MILLE SIGN
    [0x0409] = 0x8A,  -- CYRILLIC CAPITAL LETTER LJE
    [0x2039] = 0x8B,  -- SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    [0x040A] = 0x8C,  -- CYRILLIC CAPITAL LETTER NJE
    [0x040C] = 0x8D,  -- CYRILLIC CAPITAL LETTER KJE
    [0x040B] = 0x8E,  -- CYRILLIC CAPITAL LETTER TSHE
    [0x040F] = 0x8F,  -- CYRILLIC CAPITAL LETTER DZHE
    [0x0452] = 0x90,  -- CYRILLIC SMALL LETTER DJE
    [0x2018] = 0x91,  -- LEFT SINGLE QUOTATION MARK
    [0x2019] = 0x92,  -- RIGHT SINGLE QUOTATION MARK
    [0x201C] = 0x93,  -- LEFT DOUBLE QUOTATION MARK
    [0x201D] = 0x94,  -- RIGHT DOUBLE QUOTATION MARK
    [0x2022] = 0x95,  -- BULLET
    [0x2013] = 0x96,  -- EN DASH
    [0x2014] = 0x97,  -- EM DASH
    [0x2122] = 0x99,  -- TRADE MARK SIGN
    [0x0459] = 0x9A,  -- CYRILLIC SMALL LETTER LJE
    [0x203A] = 0x9B,  -- SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    [0x045A] = 0x9C,  -- CYRILLIC SMALL LETTER NJE
    [0x045C] = 0x9D,  -- CYRILLIC SMALL LETTER KJE
    [0x045B] = 0x9E,  -- CYRILLIC SMALL LETTER TSHE
    [0x045F] = 0x9F,  -- CYRILLIC SMALL LETTER DZHE
    [0x00A0] = 0xA0,  -- NO-BREAK SPACE
    [0x040E] = 0xA1,  -- CYRILLIC CAPITAL LETTER SHORT U
    [0x045E] = 0xA2,  -- CYRILLIC SMALL LETTER SHORT U
    [0x0408] = 0xA3,  -- CYRILLIC CAPITAL LETTER JE
    [0x00A4] = 0xA4,  -- CURRENCY SIGN
    [0x0490] = 0xA5,  -- CYRILLIC CAPITAL LETTER GHE WITH UPTURN
    [0x00A6] = 0xA6,  -- BROKEN BAR
    [0x00A7] = 0xA7,  -- SECTION SIGN
    [0x0401] = 0xA8,  -- CYRILLIC CAPITAL LETTER IO
    [0x00A9] = 0xA9,  -- COPYRIGHT SIGN
    [0x0404] = 0xAA,  -- CYRILLIC CAPITAL LETTER UKRAINIAN IE
    [0x00AB] = 0xAB,  -- LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
    [0x00AC] = 0xAC,  -- NOT SIGN
    [0x00AD] = 0xAD,  -- SOFT HYPHEN
    [0x00AE] = 0xAE,  -- REGISTERED SIGN
    [0x0407] = 0xAF,  -- CYRILLIC CAPITAL LETTER YI
    [0x00B0] = 0xB0,  -- DEGREE SIGN
    [0x00B1] = 0xB1,  -- PLUS-MINUS SIGN
    [0x0406] = 0xB2,  -- CYRILLIC CAPITAL LETTER BYELORUSSIAN-UKRAINIAN I
    [0x0456] = 0xB3,  -- CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I
    [0x0491] = 0xB4,  -- CYRILLIC SMALL LETTER GHE WITH UPTURN
    [0x00B5] = 0xB5,  -- MICRO SIGN
    [0x00B6] = 0xB6,  -- PILCROW SIGN
    [0x00B7] = 0xB7,  -- MIDDLE DOT
    [0x0451] = 0xB8,  -- CYRILLIC SMALL LETTER IO
    [0x2116] = 0xB9,  -- NUMERO SIGN
    [0x0454] = 0xBA,  -- CYRILLIC SMALL LETTER UKRAINIAN IE
    [0x00BB] = 0xBB,  -- RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
    [0x0458] = 0xBC,  -- CYRILLIC SMALL LETTER JE
    [0x0405] = 0xBD,  -- CYRILLIC CAPITAL LETTER DZE
    [0x0455] = 0xBE,  -- CYRILLIC SMALL LETTER DZE
    [0x0457] = 0xBF,  -- CYRILLIC SMALL LETTER YI
    [0x0410] = 0xC0,  -- CYRILLIC CAPITAL LETTER A
    [0x0411] = 0xC1,  -- CYRILLIC CAPITAL LETTER BE
    [0x0412] = 0xC2,  -- CYRILLIC CAPITAL LETTER VE
    [0x0413] = 0xC3,  -- CYRILLIC CAPITAL LETTER GHE
    [0x0414] = 0xC4,  -- CYRILLIC CAPITAL LETTER DE
    [0x0415] = 0xC5,  -- CYRILLIC CAPITAL LETTER IE
    [0x0416] = 0xC6,  -- CYRILLIC CAPITAL LETTER ZHE
    [0x0417] = 0xC7,  -- CYRILLIC CAPITAL LETTER ZE
    [0x0418] = 0xC8,  -- CYRILLIC CAPITAL LETTER I
    [0x0419] = 0xC9,  -- CYRILLIC CAPITAL LETTER SHORT I
    [0x041A] = 0xCA,  -- CYRILLIC CAPITAL LETTER KA
    [0x041B] = 0xCB,  -- CYRILLIC CAPITAL LETTER EL
    [0x041C] = 0xCC,  -- CYRILLIC CAPITAL LETTER EM
    [0x041D] = 0xCD,  -- CYRILLIC CAPITAL LETTER EN
    [0x041E] = 0xCE,  -- CYRILLIC CAPITAL LETTER O
    [0x041F] = 0xCF,  -- CYRILLIC CAPITAL LETTER PE
    [0x0420] = 0xD0,  -- CYRILLIC CAPITAL LETTER ER
    [0x0421] = 0xD1,  -- CYRILLIC CAPITAL LETTER ES
    [0x0422] = 0xD2,  -- CYRILLIC CAPITAL LETTER TE
    [0x0423] = 0xD3,  -- CYRILLIC CAPITAL LETTER U
    [0x0424] = 0xD4,  -- CYRILLIC CAPITAL LETTER EF
    [0x0425] = 0xD5,  -- CYRILLIC CAPITAL LETTER HA
    [0x0426] = 0xD6,  -- CYRILLIC CAPITAL LETTER TSE
    [0x0427] = 0xD7,  -- CYRILLIC CAPITAL LETTER CHE
    [0x0428] = 0xD8,  -- CYRILLIC CAPITAL LETTER SHA
    [0x0429] = 0xD9,  -- CYRILLIC CAPITAL LETTER SHCHA
    [0x042A] = 0xDA,  -- CYRILLIC CAPITAL LETTER HARD SIGN
    [0x042B] = 0xDB,  -- CYRILLIC CAPITAL LETTER YERU
    [0x042C] = 0xDC,  -- CYRILLIC CAPITAL LETTER SOFT SIGN
    [0x042D] = 0xDD,  -- CYRILLIC CAPITAL LETTER E
    [0x042E] = 0xDE,  -- CYRILLIC CAPITAL LETTER YU
    [0x042F] = 0xDF,  -- CYRILLIC CAPITAL LETTER YA
    [0x0430] = 0xE0,  -- CYRILLIC SMALL LETTER A
    [0x0431] = 0xE1,  -- CYRILLIC SMALL LETTER BE
    [0x0432] = 0xE2,  -- CYRILLIC SMALL LETTER VE
    [0x0433] = 0xE3,  -- CYRILLIC SMALL LETTER GHE
    [0x0434] = 0xE4,  -- CYRILLIC SMALL LETTER DE
    [0x0435] = 0xE5,  -- CYRILLIC SMALL LETTER IE
    [0x0436] = 0xE6,  -- CYRILLIC SMALL LETTER ZHE
    [0x0437] = 0xE7,  -- CYRILLIC SMALL LETTER ZE
    [0x0438] = 0xE8,  -- CYRILLIC SMALL LETTER I
    [0x0439] = 0xE9,  -- CYRILLIC SMALL LETTER SHORT I
    [0x043A] = 0xEA,  -- CYRILLIC SMALL LETTER KA
    [0x043B] = 0xEB,  -- CYRILLIC SMALL LETTER EL
    [0x043C] = 0xEC,  -- CYRILLIC SMALL LETTER EM
    [0x043D] = 0xED,  -- CYRILLIC SMALL LETTER EN
    [0x043E] = 0xEE,  -- CYRILLIC SMALL LETTER O
    [0x043F] = 0xEF,  -- CYRILLIC SMALL LETTER PE
    [0x0440] = 0xF0,  -- CYRILLIC SMALL LETTER ER
    [0x0441] = 0xF1,  -- CYRILLIC SMALL LETTER ES
    [0x0442] = 0xF2,  -- CYRILLIC SMALL LETTER TE
    [0x0443] = 0xF3,  -- CYRILLIC SMALL LETTER U
    [0x0444] = 0xF4,  -- CYRILLIC SMALL LETTER EF
    [0x0445] = 0xF5,  -- CYRILLIC SMALL LETTER HA
    [0x0446] = 0xF6,  -- CYRILLIC SMALL LETTER TSE
    [0x0447] = 0xF7,  -- CYRILLIC SMALL LETTER CHE
    [0x0448] = 0xF8,  -- CYRILLIC SMALL LETTER SHA
    [0x0449] = 0xF9,  -- CYRILLIC SMALL LETTER SHCHA
    [0x044A] = 0xFA,  -- CYRILLIC SMALL LETTER HARD SIGN
    [0x044B] = 0xFB,  -- CYRILLIC SMALL LETTER YERU
    [0x044C] = 0xFC,  -- CYRILLIC SMALL LETTER SOFT SIGN
    [0x044D] = 0xFD,  -- CYRILLIC SMALL LETTER E
    [0x044E] = 0xFE,  -- CYRILLIC SMALL LETTER YU
    [0x044F] = 0xFF,  -- CYRILLIC SMALL LETTER YA
  }

local function utf8_to_unicode(utf8str, pos)
    -- pos = starting byte position inside input string (default 1)
    pos = pos or 1
    local code, size = string.byte(utf8str, pos), 1
    if code >= 0xC0 and code < 0xFE then
        local mask = 64
        code = code - 128
        repeat
            local next_byte = string.byte(utf8str, pos + size) or 0
            if next_byte >= 0x80 and next_byte < 0xC0 then
                code, size = (code - mask - 2) * 64 + next_byte, size + 1
            else
                code, size = string.byte(utf8str, pos), 1
            end
            mask = mask * 32
        until code < mask
    end
    -- returns code, number of bytes in this utf8 char
    return code, size
end

function utf8_to_codepage(utf8str)
    local pos, result_codepage = 1, {}
    while pos <= #utf8str do
        local code, size = utf8_to_unicode(utf8str, pos)
        pos = pos + size
        code = code < 128 and code or CP1251[code] or string.byte("?")
        table.insert(result_codepage, string.char(code))
    end
    return table.concat(result_codepage)
end

--------------------------------------------------------------------------------------------------------------------------------------------------------------

local json = { _version = "0.1.2" }

-------------------------------------------------------------------------------
-- Encode
-------------------------------------------------------------------------------

local encode

local escape_char_map = {
  [ "\\" ] = "\\",
  [ "\"" ] = "\"",
  [ "\b" ] = "b",
  [ "\f" ] = "f",
  [ "\n" ] = "n",
  [ "\r" ] = "r",
  [ "\t" ] = "t",
}

local escape_char_map_inv = { [ "/" ] = "/" }
for k, v in pairs(escape_char_map) do
  escape_char_map_inv[v] = k
end


local function escape_char(c)
  return "\\" .. (escape_char_map[c] or string.format("u%04x", c:byte()))
end


local function encode_nil(val)
  return "null"
end


local function encode_table(val, stack)
  local res = {}
  stack = stack or {}

  -- Circular reference?
  if stack[val] then error("circular reference") end

  stack[val] = true

  if rawget(val, 1) ~= nil or next(val) == nil then
    -- Treat as array -- check keys are valid and it is not sparse
    local n = 0
    for k in pairs(val) do
      if type(k) ~= "number" then
        error("invalid table: mixed or invalid key types")
      end
      n = n + 1
    end
    if n ~= #val then
      error("invalid table: sparse array")
    end
    -- Encode
    for i, v in ipairs(val) do
      table.insert(res, encode(v, stack))
    end
    stack[val] = nil
    return "[" .. table.concat(res, ",") .. "]"

  else
    -- Treat as an object
    for k, v in pairs(val) do
      if type(k) ~= "string" then
        error("invalid table: mixed or invalid key types")
      end
      table.insert(res, encode(k, stack) .. ":" .. encode(v, stack))
    end
    stack[val] = nil
    return "{" .. table.concat(res, ",") .. "}"
  end
end


local function encode_string(val)
  return '"' .. val:gsub('[%z\1-\31\\"]', escape_char) .. '"'
end


local function encode_number(val)
  -- Check for NaN, -inf and inf
  if val ~= val or val <= -math.huge or val >= math.huge then
    error("unexpected number value '" .. tostring(val) .. "'")
  end
  return string.format("%.14g", val)
end


local type_func_map = {
  [ "nil"     ] = encode_nil,
  [ "table"   ] = encode_table,
  [ "string"  ] = encode_string,
  [ "number"  ] = encode_number,
  [ "boolean" ] = tostring,
}


encode = function(val, stack)
  local t = type(val)
  local f = type_func_map[t]
  if f then
    return f(val, stack)
  end
  error("unexpected type '" .. t .. "'")
end


function json.encode(val)
  return ( encode(val) )
end


-------------------------------------------------------------------------------
-- Decode
-------------------------------------------------------------------------------

local parse

local function create_set(...)
  local res = {}
  for i = 1, select("#", ...) do
    res[ select(i, ...) ] = true
  end
  return res
end

local space_chars   = create_set(" ", "\t", "\r", "\n")
local delim_chars   = create_set(" ", "\t", "\r", "\n", "]", "}", ",")
local escape_chars  = create_set("\\", "/", '"', "b", "f", "n", "r", "t", "u")
local literals      = create_set("true", "false", "null")

local literal_map = {
  [ "true"  ] = true,
  [ "false" ] = false,
  [ "null"  ] = nil,
}


local function next_char(str, idx, set, negate)
  for i = idx, #str do
    if set[str:sub(i, i)] ~= negate then
      return i
    end
  end
  return #str + 1
end


local function decode_error(str, idx, msg)
  local line_count = 1
  local col_count = 1
  for i = 1, idx - 1 do
    col_count = col_count + 1
    if str:sub(i, i) == "\n" then
      line_count = line_count + 1
      col_count = 1
    end
  end
  error( string.format("%s at line %d col %d", msg, line_count, col_count) )
end


local function codepoint_to_utf8(n)
  -- http://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=iws-appendixa
  local f = math.floor
  if n <= 0x7f then
    return string.char(n)
  elseif n <= 0x7ff then
    return string.char(f(n / 64) + 192, n % 64 + 128)
  elseif n <= 0xffff then
    return string.char(f(n / 4096) + 224, f(n % 4096 / 64) + 128, n % 64 + 128)
  elseif n <= 0x10ffff then
    return string.char(f(n / 262144) + 240, f(n % 262144 / 4096) + 128,
                       f(n % 4096 / 64) + 128, n % 64 + 128)
  end
  error( string.format("invalid unicode codepoint '%x'", n) )
end


local function parse_unicode_escape(s)
  local n1 = tonumber( s:sub(1, 4),  16 )
  local n2 = tonumber( s:sub(7, 10), 16 )
   -- Surrogate pair?
  if n2 then
    return codepoint_to_utf8((n1 - 0xd800) * 0x400 + (n2 - 0xdc00) + 0x10000)
  else
    return codepoint_to_utf8(n1)
  end
end


local function parse_string(str, i)
  local res = ""
  local j = i + 1
  local k = j

  while j <= #str do
    local x = str:byte(j)

    if x < 32 then
      decode_error(str, j, "control character in string")

    elseif x == 92 then -- `\`: Escape
      res = res .. str:sub(k, j - 1)
      j = j + 1
      local c = str:sub(j, j)
      if c == "u" then
        local hex = str:match("^[dD][89aAbB]%x%x\\u%x%x%x%x", j + 1)
                 or str:match("^%x%x%x%x", j + 1)
                 or decode_error(str, j - 1, "invalid unicode escape in string")
        res = res .. parse_unicode_escape(hex)
        j = j + #hex
      else
        if not escape_chars[c] then
          decode_error(str, j - 1, "invalid escape char '" .. c .. "' in string")
        end
        res = res .. escape_char_map_inv[c]
      end
      k = j + 1

    elseif x == 34 then -- `"`: End of string
      res = res .. str:sub(k, j - 1)
      res = utf8_to_codepage(res)
      return res, j + 1
    end

    j = j + 1
  end

  decode_error(str, i, "expected closing quote for string")
end


local function parse_number(str, i)
  local x = next_char(str, i, delim_chars)
  local s = str:sub(i, x - 1)
  local n = tonumber(s)
  if not n then
    decode_error(str, i, "invalid number '" .. s .. "'")
  end
  return n, x
end


local function parse_literal(str, i)
  local x = next_char(str, i, delim_chars)
  local word = str:sub(i, x - 1)
  if not literals[word] then
    decode_error(str, i, "invalid literal '" .. word .. "'")
  end
  return literal_map[word], x
end


local function parse_array(str, i)
  local res = {}
  local n = 1
  i = i + 1
  while 1 do
    local x
    i = next_char(str, i, space_chars, true)
    -- Empty / end of array?
    if str:sub(i, i) == "]" then
      i = i + 1
      break
    end
    -- Read token
    x, i = parse(str, i)
    res[n] = x
    n = n + 1
    -- Next token
    i = next_char(str, i, space_chars, true)
    local chr = str:sub(i, i)
    i = i + 1
    if chr == "]" then break end
    if chr ~= "," then decode_error(str, i, "expected ']' or ','") end
  end
  return res, i
end


local function parse_object(str, i)
  local res = {}
  i = i + 1
  while 1 do
    local key, val
    i = next_char(str, i, space_chars, true)
    -- Empty / end of object?
    if str:sub(i, i) == "}" then
      i = i + 1
      break
    end
    -- Read key
    if str:sub(i, i) ~= '"' then
      decode_error(str, i, "expected string for key")
    end
    key, i = parse(str, i)
    -- Read ':' delimiter
    i = next_char(str, i, space_chars, true)
    if str:sub(i, i) ~= ":" then
      decode_error(str, i, "expected ':' after key")
    end
    i = next_char(str, i + 1, space_chars, true)
    -- Read value
    val, i = parse(str, i)
    -- Set
    res[key] = val
    -- Next token
    i = next_char(str, i, space_chars, true)
    local chr = str:sub(i, i)
    i = i + 1
    if chr == "}" then break end
    if chr ~= "," then decode_error(str, i, "expected '}' or ','") end
  end
  return res, i
end


local char_func_map = {
  [ '"' ] = parse_string,
  [ "0" ] = parse_number,
  [ "1" ] = parse_number,
  [ "2" ] = parse_number,
  [ "3" ] = parse_number,
  [ "4" ] = parse_number,
  [ "5" ] = parse_number,
  [ "6" ] = parse_number,
  [ "7" ] = parse_number,
  [ "8" ] = parse_number,
  [ "9" ] = parse_number,
  [ "-" ] = parse_number,
  [ "t" ] = parse_literal,
  [ "f" ] = parse_literal,
  [ "n" ] = parse_literal,
  [ "[" ] = parse_array,
  [ "{" ] = parse_object,
}


parse = function(str, idx)
  local chr = str:sub(idx, idx)
  local f = char_func_map[chr]
  if f then
    return f(str, idx)
  end
  decode_error(str, idx, "unexpected character '" .. chr .. "'")
end


-- STALKER formatting issues
local function replaceSpecialCharacters(str)
  -- Replace en dash and em dash with standard hyphen
  str = str:gsub("\226\128\147", " - ") -- en dash
  str = str:gsub("\226\128\148", " - ") -- em dash
  -- Replace left single quotation mark and right single quotation mark with standard apostrophe
  str = str:gsub("\226\128\152", "'") -- left single quotation mark
  str = str:gsub("\226\128\153", "'") -- right single quotation mark
  -- Replace left double quotation mark and right double quotation mark with standard quotes
  str = str:gsub("\226\128\156", '"') -- left double quotation mark
  str = str:gsub("\226\128\157", '"') -- right double quotation mark
  return str
end


-- Modify the json.decode function
function json.decode(str)
    if type(str) ~= "string" then
        error("expected argument of type string, got " .. type(str))
    end
    -- Preprocess the string to replace special characters
    str = replaceSpecialCharacters(str)

    local res, idx = parse(str, next_char(str, 1, space_chars, true))
    idx = next_char(str, idx, space_chars, true)
    if idx <= #str then
        decode_error(str, idx, "trailing garbage")
    end
    return res
end

local function convert_to_utf8(text)
    if not text then return nil end

    -- Create reverse mapping from CP1251 to Unicode
    local CP1251_to_unicode = {}
    for unicode, cp1251 in pairs(CP1251) do
        CP1251_to_unicode[cp1251] = unicode
    end

    local result = {}
    for i = 1, #text do
        local byte = text:byte(i)
        if byte < 128 then
            table.insert(result, string.char(byte))
        else
            local unicode = CP1251_to_unicode[byte]
            if unicode then
                if unicode <= 0x7F then
                    table.insert(result, string.char(unicode))
                elseif unicode <= 0x7FF then
                    table.insert(result, string.char(0xC0 + math.floor(unicode / 64)))
                    table.insert(result, string.char(0x80 + (unicode % 64)))
                else
                    table.insert(result, string.char(0xE0 + math.floor(unicode / 4096)))
                    table.insert(result, string.char(0x80 + math.floor((unicode % 4096) / 64)))
                    table.insert(result, string.char(0x80 + (unicode % 64)))
                end
            end
        end
    end
    return table.concat(result)
end

function json.convert_to_utf8(text)
    if type(text) ~= "string" then
        error("expected argument of type string, got " .. type(text))
    end

    -- Convert CP1251 encoded text to UTF-8
    local utf8_text = convert_to_utf8(text)

    -- If the conversion fails, return nil
    if not utf8_text then
        return nil
    end

    -- Return the UTF-8 encoded text
    return utf8_text
end

function json.utf8_to_codepage(utf8str)
    if type(utf8str) ~= "string" then
        error("expected argument of type string, got " .. type(utf8str))
    end

    -- Convert UTF-8 encoded text to CP1251
    local cp1251_text = utf8_to_codepage(utf8str)

    -- If the conversion fails, return nil
    if not cp1251_text then
        return nil
    end

    -- Return the CP1251 encoded text
    return cp1251_text
end

return json
