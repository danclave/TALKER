# test_tui_flows.py - TUI flow tests with injected keys (no real terminal needed)
import io
import sys

from rich.console import Console

import tui_old as tui
from settings import load_settings


def fresh():
    st = load_settings()
    st["language"] = "en"
    st["vosk_model_overrides"] = {}
    return st


def make_console():
    return Console(file=io.StringIO(), force_terminal=False, width=110)


# Flow 1: navigate to language, search 'ru', pick Russian, choose model 0.22, start
st = fresh()
script = ["down", "down", "down", "enter", "r", "u", "enter", "down", "enter", "enter"]
buf = io.StringIO()
result = tui.run_tui(st, on_test=None, console=make_console(),
                     key_source=tui.FakeKeySource(script))
assert result["language"] == "ru", result
assert result["vosk_model_overrides"].get("ru") == "vosk-model-small-ru-0.22", result
print("FLOW 1 OK: nav + search + ru model choice + start")

# Flow 2: gemini chain - move first model down (3.1 becomes first), done, start
st = fresh()
st["provider"] = "gemini_proxy"
script = ["down", "down", "down", "down", "down", "enter",  # to 'Gemini voice models'
          "d",                      # move 3.5-flash-lite down
          "enter",                  # Done
          "enter"]                  # Start
result = tui.run_tui(st, on_test=None, console=make_console(),
                     key_source=tui.FakeKeySource(script))
assert result["gemini_models"][0] == "gemini/gemini-3.1-flash-lite", result["gemini_models"]
print("FLOW 2 OK: gemini reorder -> 3.1 first")

# Flow 3: pinned order - search blank lists all, first entries must be pinned
codes = None
import languages
codes = languages.language_display_order()
assert codes[:6] == ["en", "en-gb", "ru", "uk", "pl", "es"], codes[:6]
print("FLOW 3 OK: pinned order", codes[:6])

# Flow 4: escape from language picker returns without change
st = fresh()
script = ["down", "down", "down", "enter", "escape", "enter"]
result = tui.run_tui(st, on_test=None, console=make_console(),
                     key_source=tui.FakeKeySource(script))
assert result["language"] == "en", result
print("FLOW 4 OK: escape cancels language change")

print("ALL TUI FLOWS PASSED")
