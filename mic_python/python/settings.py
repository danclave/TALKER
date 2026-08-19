# settings.py
# persistent mic app settings + interactive configuration menu
# settings are stored next to the executable/script as talker_mic_settings.json

import json
import sys
from pathlib import Path

from languages import LANGUAGES, language_display_order, language_name

ROOT_DIR = Path(getattr(sys, "frozen", False) and sys.executable or __file__).resolve().parent
SETTINGS_FILE = ROOT_DIR / "talker_mic_settings.json"

# Selectable providers in the menu (whisper_api stays CLI-only for compatibility)
PROVIDERS = {
    "whisper_local": "Whisper local  - offline, 99 languages, best accuracy",
    "vosk_local":    "Vosk local     - offline, ultra-light (~40 MB models)",
    "gemini_proxy":  "Gemini proxy   - best quality, requires the API proxy",
}

WHISPER_MODELS = {
    "tiny":            "tiny            ~75 MB   fastest, lowest accuracy",
    "base":            "base            ~145 MB  fast, decent accuracy",
    "small":           "small           ~490 MB  recommended balance",
    "medium":          "medium          ~1.5 GB  accurate, slower",
    "large-v3-turbo":  "large-v3-turbo  ~1.6 GB  best accuracy, needs strong CPU",
}

GEMINI_VOICE_MODES = [
    ("gemini/gemini-3.5-flash-lite", "newest, fastest, improved ASR"),
    ("gemini/gemini-3.1-flash-lite", "previous gen, very reliable ASR"),
]

DEFAULT_SETTINGS = {
    "provider": "whisper_local",
    "language": "en",
    "whisper_model": "small",
    "gemini_models": ["gemini/gemini-3.5-flash-lite", "gemini/gemini-3.1-flash-lite"],
}

VALID_PROVIDERS = list(PROVIDERS) + ["whisper_api"]


################################################################################################
# LOAD / SAVE
################################################################################################

def load_settings():
    settings = dict(DEFAULT_SETTINGS)
    try:
        if SETTINGS_FILE.exists():
            stored = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                settings.update(stored)
    except Exception as e:
        print(f"[WARN] Could not read settings ({e}), using defaults.")
    # sanitize
    if settings.get("provider") not in VALID_PROVIDERS:
        settings["provider"] = DEFAULT_SETTINGS["provider"]
    if settings.get("language") not in LANGUAGES:
        settings["language"] = DEFAULT_SETTINGS["language"]
    if settings.get("whisper_model") not in WHISPER_MODELS:
        settings["whisper_model"] = DEFAULT_SETTINGS["whisper_model"]
    if not isinstance(settings.get("gemini_models"), list) or not settings["gemini_models"]:
        settings["gemini_models"] = list(DEFAULT_SETTINGS["gemini_models"])
    return settings


def save_settings(settings):
    try:
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
        print(f"Settings saved to {SETTINGS_FILE}")
    except Exception as e:
        print(f"[ERROR] Could not save settings: {e}")


################################################################################################
# MENU HELPERS
################################################################################################

def _input(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        print("\n[EOF] No more input - exiting.")
        raise SystemExit(0)


def _pick_from_list(entries, title):
    """Show a numbered list, return the chosen index (0-based) or None on cancel."""
    while True:
        print(f"\n  {title}")
        for i, entry in enumerate(entries, 1):
            print(f"    {i}) {entry}")
        choice = _input("  Select number (blank = back): ")
        if choice == "":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(entries):
            return int(choice) - 1
        print("  Invalid choice.")


def pick_language(current):
    """Searchable language picker. EN/RU first, then the rest alphabetically."""
    code = current
    while True:
        query = _input("\n  Language search (name or code, blank = list all, '-' = back): ").lower()
        if query == "-":
            return code
        matches = [
            c for c in language_display_order()
            if query == "" or query in LANGUAGES[c].lower() or query in c
        ]
        if not matches:
            print("  No language matches that search.")
            continue
        entries = [f"{LANGUAGES[c]} ({c})" + ("  [current]" if c == current else "")
                   for c in matches]
        pick = _pick_from_list(entries, f"Languages ({len(matches)} found)")
        if pick is not None:
            code = matches[pick]
            print(f"  Language set to: {LANGUAGES[code]} ({code})")
            return code


def pick_whisper_model(current):
    entries = [
        desc + ("  [current]" if name == current else "")
        for name, desc in WHISPER_MODELS.items()
    ]
    pick = _pick_from_list(entries, "Whisper model size")
    if pick is None:
        return current
    name = list(WHISPER_MODELS)[pick]
    print(f"  Whisper model set to: {name}")
    return name


def pick_gemini_models(current_chain):
    """Multi-select + reorder the static list of voice-capable Gemini models."""
    selected = [m for m in current_chain if any(m == cand for cand, _ in GEMINI_VOICE_MODES)]
    unselected = [m for m, _ in GEMINI_VOICE_MODES if m not in selected]
    selected = selected + unselected  # every candidate visible; selection = membership

    while True:
        print("\n  Gemini voice models (used top-down as fallback chain)")
        print("  <n> toggle | u <n> move up | d <n> move down | Enter = done")
        for i, model in enumerate(selected, 1):
            known = next((d for m, d in GEMINI_VOICE_MODES if m == model), "")
            mark = "x" if model in current_chain else " "
            print(f"    {i}) [{mark}] {model}  - {known}")

        cmd = _input("  > ").strip()
        if cmd == "":
            chain = [m for m in selected if m in current_chain]
            if not chain:
                print("  At least one model must be selected.")
                continue
            print("  Fallback chain: " + " -> ".join(chain))
            return chain
        parts = cmd.split()
        try:
            if len(parts) == 2 and parts[0] in ("u", "d") and parts[1].isdigit():
                idx = int(parts[1]) - 1
                if not 0 <= idx < len(selected):
                    raise IndexError
                step = -1 if parts[0] == "u" else 1
                j = idx + step
                if 0 <= j < len(selected):
                    selected[idx], selected[j] = selected[j], selected[idx]
                else:
                    print("  Already at the edge.")
            elif len(parts) == 1 and parts[0].isdigit():
                idx = int(parts[0]) - 1
                if not 0 <= idx < len(selected):
                    raise IndexError
                model = selected[idx]
                if model in current_chain:
                    if sum(m in current_chain for m in selected) <= 1:
                        print("  At least one model must stay selected.")
                        continue
                    current_chain.remove(model)
                else:
                    current_chain.append(model)
            else:
                print("  Invalid command.")
        except (IndexError, ValueError):
            print("  Invalid number.")


################################################################################################
# MAIN MENU
################################################################################################

def _summary(settings):
    provider = PROVIDERS.get(settings["provider"], settings["provider"])
    lang = f"{language_name(settings['language'])} ({settings['language']})"
    lines = [
        f"  Provider : {provider}",
        f"  Language : {lang}",
    ]
    if settings["provider"] == "whisper_local":
        lines.append(f"  Whisper  : {settings['whisper_model']}")
    if settings["provider"] == "gemini_proxy":
        lines.append(f"  Gemini   : {' -> '.join(m.split('/')[-1] for m in settings['gemini_models'])}")
    return lines


def run_menu(settings):
    """Interactive menu. Mutates and returns the settings dict."""
    print("=" * 50)
    print(" TALKER Mic - Configuration")
    print("=" * 50)

    while True:
        print("\n".join(_summary(settings)))
        print()
        print("  1) Start")
        print("  2) Save settings")
        print("  3) Change provider")
        print("  4) Change language")
        print("  5) Whisper model size")
        print("  6) Gemini voice models")
        print("  0) Exit")
        choice = _input("  Select: ")

        if choice == "1":
            return settings, False
        elif choice == "2":
            save_settings(settings)
        elif choice == "3":
            entries = [desc + ("  [current]" if key == settings["provider"] else "")
                       for key, desc in PROVIDERS.items()]
            pick = _pick_from_list(entries, "Transcription provider")
            if pick is not None:
                settings["provider"] = list(PROVIDERS)[pick]
        elif choice == "4":
            settings["language"] = pick_language(settings["language"])
        elif choice == "5":
            settings["whisper_model"] = pick_whisper_model(settings["whisper_model"])
        elif choice == "6":
            settings["gemini_models"] = pick_gemini_models(list(settings["gemini_models"]))
        elif choice == "0":
            print("Exiting without starting the microphone service.")
            raise SystemExit(0)
        else:
            print("  Invalid choice.")
