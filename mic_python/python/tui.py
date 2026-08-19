# tui.py
# interactive terminal UI for the TALKER mic app
# rich for rendering, prompt_toolkit for raw key input
# arrow-key navigation, type-to-search, multi-select with reordering

import sys
from types import SimpleNamespace

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from languages import (LANGUAGES, language_display_order, vosk_model_options,
                       vosk_model_info, whisper_supported, VOSK_BIG_MB)
import models_manager

ESC = "\x1b"


################################################################################################
# KEY INPUT
################################################################################################

def _normalize_key(key):
    """Map a prompt_toolkit key to a simple string: up/down/enter/escape/... or a char."""
    mapping = {
        "up": "up", "down": "down", "left": "left", "right": "right",
        "enter": "enter", "escape": "escape", "backspace": "backspace",
        "space": "space", "home": "home", "end": "end",
        "pageup": "pgup", "pagedown": "pgdn", "delete": "delete",
        "s-up": "shift-up", "s-down": "shift-down",
        "c-c": "ctrl-c", "c-d": "ctrl-d", "tab": "tab",
    }
    name = str(key)
    if name in mapping:
        return mapping[name]
    if len(name) == 1:
        return name
    return None


class KeySourceExhausted(Exception):
    """Raised when the key stream ends (window closed / stdin gone)."""


class RealKeySource:
    """Reads keys from the real terminal via prompt_toolkit (one long-lived stream)."""

    def __init__(self):
        from prompt_toolkit.input import create_input
        self._input = create_input()
        self._gen = self._gen_keys()

    def _gen_keys(self):
        with self._input.raw_mode():
            while True:
                try:
                    key_press = self._input.read_keys()
                except Exception:
                    return  # stdin closed (window X / terminal gone)
                if not key_press:
                    return
                yield SimpleNamespace(key=_normalize_key(key_press.key))

    def keys(self):
        return self._gen


class FakeKeySource:
    """Replays a scripted list of normalized key names (for tests)."""

    def __init__(self, script):
        self._gen = (SimpleNamespace(key=k) for k in script)

    def keys(self):
        return self._gen


def get_key(key_source):
    """Next key press, or None when the key stream has ended."""
    try:
        return next(key_source.keys()).key
    except StopIteration:
        return None


################################################################################################
# RENDER HELPERS
################################################################################################

STYLE_TITLE = "bold cyan"
STYLE_SEL = "bold black on cyan"
STYLE_HINT = "dim"
STYLE_WARN = "bold red"
STYLE_GOOD = "green"
STYLE_TAG_VOSK = "green"
STYLE_TAG_WHISPER = "cyan"
STYLE_TAG_BAD = "red"

PAGE_SIZE = 14


def _clear(console):
    console.file.write("\x1b[2J\x1b[3J\x1b[H")
    console.file.flush()


def _menu_rows(items, selected):
    """items: list of markup label strings. Returns Text rows with selection marker."""
    rows = []
    for i, label in enumerate(items):
        marker = "❯ " if i == selected else "  "
        row = Text()
        row.append(marker, "bold cyan" if i == selected else "dim")
        try:
            row.append(Text.from_markup(label))
        except Exception:
            row.append(label)
        if i == selected:
            row.stylize("bold")
        rows.append(row)
    return rows


def _window(rows, selected):
    """Return a slice of rows centered sensibly around the selection."""
    if len(rows) <= PAGE_SIZE:
        return rows, selected, 0
    start = max(0, min(selected - PAGE_SIZE // 2, len(rows) - PAGE_SIZE))
    return rows[start:start + PAGE_SIZE], selected - start, start


def _footer(*pairs):
    parts = []
    for key, action in pairs:
        parts.append(f"[bold]{key}[/bold] {action}")
    return Text.from_markup("  ·  ".join(parts), style=STYLE_HINT)


def _provider_label(key, desc):
    if "RECOMMENDED" in desc:
        return f"[bold yellow]{desc}[/]"
    return desc


def _language_tag(code, overrides):
    info = vosk_model_info(code)
    if info:
        tag = f"vosk ~{info[1]} MB"
        style = STYLE_TAG_VOSK
        if info[1] >= VOSK_BIG_MB:
            tag += " BIG"
            style = "yellow"
        options = vosk_model_options(code)
        if len(options) > 1:
            tag += f" · {len(options)} models"
        if overrides.get(code):
            tag += f" · {overrides[code]}"
    else:
        tag, style = "no vosk", STYLE_TAG_BAD
    wtag = "whisper" if whisper_supported(code) else "no whisper"
    wstyle = STYLE_TAG_WHISPER if whisper_supported(code) else STYLE_TAG_BAD
    return f"[{style}]{tag}[/]  [{wstyle}]{wtag}[/]"


def _summary_lines(settings):
    provider = settings["provider"]
    lines = [
        ("Provider", provider.replace("_", " ").upper()),
        ("Language", f"{LANGUAGES.get(settings['language'], settings['language'])} ({settings['language']})"),
    ]
    if provider == "whisper_local":
        lines.append(("Whisper", settings["whisper_model"]))
    if provider == "gemini_proxy":
        lines.append(("Gemini chain", "\n  ".join(m.split("/")[-1] for m in settings["gemini_models"])))
    if provider == "vosk_local":
        override = (settings.get("vosk_model_overrides") or {}).get(settings["language"])
        if override:
            lines.append(("Vosk model", override))
    return lines


################################################################################################
# VIEWS
################################################################################################

def _home_view(console, settings, unsaved):
    left = Table.grid(padding=(0, 2))
    left.add_column(style="dim", justify="right")
    left.add_column()
    for name, value in _summary_lines(settings):
        left.add_row(name + ":", value)
    if unsaved:
        left.add_row("", "[yellow]* unsaved changes[/]")
    vosk_count = len(models_manager.list_vosk_models())
    whisper_count = len(models_manager.list_whisper_models())
    left.add_row("", "")
    left.add_row("On disk:", f"{vosk_count} vosk · {whisper_count} whisper models cached")

    items = [
        "[bold green]Start the microphone service[/]",
        "Test transcription  (speak into your mic)",
        "Change transcription provider",
        "Change language",
        "Whisper model size",
        "Gemini voice models (fallback chain)",
        "Manage downloaded models",
        "Save settings",
        "[red]Exit[/]",
    ]
    return left, items


HOME_ACTIONS = ["start", "test", "provider", "language", "whisper", "gemini", "manager", "save", "exit"]


def _pick_list(console, key_source, title, items, footer=None):
    """Generic list picker. items: list of markup label strings.

    Returns selected index, or None on escape/quit.
    """
    selected = 0
    while True:
        rows = _menu_rows(items, selected)
        win, sel_in_win, _ = _window(rows, selected)
        body = Table.grid(padding=(0, 1))
        body.add_column()
        for r in win:
            body.add_row(r)
        panel = Panel(
            Group(body),
            title=f"[{STYLE_TITLE}]{title}[/]",
            box=box.ROUNDED,
            border_style="blue",
        )
        foot = footer or _footer(("↑↓", "move"), ("Enter", "select"), ("Esc", "back"), ("q", "quit"))
        _clear(console)
        console.print(panel)
        console.print(foot, justify="center")

        key = get_key(key_source)
        if key is None:
            return None  # key stream ended (window closed)
        if key in ("up", "k"):
            selected = (selected - 1) % len(items)
        elif key in ("down", "j"):
            selected = (selected + 1) % len(items)
        elif key in ("pgup",):
            selected = max(0, selected - PAGE_SIZE)
        elif key in ("pgdn",):
            selected = min(len(items) - 1, selected + PAGE_SIZE)
        elif key in ("home",):
            selected = 0
        elif key in ("end",):
            selected = len(items) - 1
        elif key == "enter":
            return selected
        elif key in ("escape", "q", "ctrl-c", "ctrl-d"):
            return None


def _language_picker(console, key_source, settings):
    """Searchable language browser with engine support tags.

    Mutates settings in place; returns True if language changed.
    """
    search = ""
    selected = 0
    overrides = settings.setdefault("vosk_model_overrides", {})
    while True:
        all_codes = language_display_order()
        matches = [
            c for c in all_codes
            if search == "" or search in LANGUAGES[c].lower() or search in c
        ]
        if not matches:
            matches = all_codes
        selected = min(selected, len(matches) - 1)
        rows = []
        for c in matches:
            label = f"{LANGUAGES[c]} [dim]({c})[/]"
            if c == settings["language"]:
                label += " [bold cyan]• current[/]"
            rows.append(f"{label}  {_language_tag(c, overrides)}")

        win, sel_in_win, start_idx = _window(
            [Text.from_markup(r) for r in rows], selected)
        body = Table.grid(padding=(0, 1))
        body.add_column()
        for r in win:
            body.add_row(r)

        search_row = Text.assemble(("Search: ", "bold"),
                                    search if search else Text("filter by name or code...", style="dim"))
        header = Table.grid(padding=(0, 1))
        header.add_column()
        header.add_row(search_row)
        header.add_row(Rule(style="dim"))

        panel = Panel(
            Group(header, body),
            title=f"[{STYLE_TITLE}]Language  ·  {len(matches)} of {len(all_codes)}[/]",
            box=box.ROUNDED,
            border_style="blue",
        )
        _clear(console)
        console.print(panel)
        console.print(_footer(("type", "filter"), ("↑↓", "move"), ("Enter", "select"),
                                   ("Esc", "back"), ("q", "quit")), justify="center")

        key = get_key(key_source)
        if key is None:
            return False  # stream ended
        if key in ("up",):
            selected = (selected - 1) % len(matches)
        elif key in ("down",):
            selected = (selected + 1) % len(matches)
        elif key in ("pgup",):
            selected = max(0, selected - PAGE_SIZE)
        elif key in ("pgdn",):
            selected = min(len(matches) - 1, selected + PAGE_SIZE)
        elif key in ("home",):
            selected = 0
        elif key in ("end",):
            selected = len(matches) - 1
        elif key == "backspace":
            search = search[:-1]
            selected = 0
        elif key == "enter":
            code = matches[selected]
            settings["language"] = code
            options = vosk_model_options(code)
            if len(options) > 1:
                pick = _model_picker(console, key_source, code, overrides)
            return True
        elif key in ("escape",):
            return False
        elif key in ("q", "ctrl-c", "ctrl-d"):
            raise SystemExit(0)
        elif isinstance(key, str) and key.isprintable():
            search += key
            selected = 0


def _model_picker(console, key_source, code, overrides):
    """Choose between multiple vosk models for a language."""
    options = vosk_model_options(code)
    selected = 0
    while True:
        rows = []
        for i, (name, size) in enumerate(options):
            label = f"{name}  [dim]~{size} MB[/]"
            if i == 0:
                label += "  [green]latest[/]"
            if overrides.get(code) == name:
                label += "  [bold cyan]• current[/]"
            rows.append(label)
        result = _pick_list(console, key_source, f"Vosk models for {LANGUAGES[code]}", rows)
        if result is None:
            return None
        i = result
        if i == 0:
            overrides.pop(code, None)
        else:
            overrides[code] = options[i][0]
        return overrides.get(code)


def _whisper_picker(console, key_source, settings):
    from settings import WHISPER_MODELS
    rows = []
    for name, desc in WHISPER_MODELS.items():
        label = f"[bold]{name}[/]  {desc}"
        if "NOT RECOMMENDED" in desc:
            label = f"[red]{name}[/]  {desc}"
        marker = " [bold cyan]• current[/]" if name == settings["whisper_model"] else ""
        rows.append(label + marker)
    result = _pick_list(console, key_source, "Whisper model size", rows,
                        footer=_footer(("↑↓", "move"), ("Enter", "select"), ("Esc", "back")))
    if result is not None:
        settings["whisper_model"] = list(WHISPER_MODELS)[result]


def _gemini_picker(console, key_source, settings):
    """Multi-select with reordering for the gemini voice model chain."""
    from settings import GEMINI_VOICE_MODES as GEMINI_VOICE_MODELS
    candidates = [m for m, _ in GEMINI_VOICE_MODELS]
    descriptions = dict(GEMINI_VOICE_MODELS)

    order = [m for m in settings["gemini_models"] if m in candidates]
    order += [m for m in candidates if m not in order]
    selected = 0
    while True:
        rows = []
        for i, m in enumerate(order):
            active = m in settings["gemini_models"]
            check = "[green]◉[/]" if active else "[dim]○[/]"
            pos = f"[dim]{i + 1}.[/]"
            rows.append(f"{pos} {check} [bold]{m.split('/')[-1]}[/]  [dim]{descriptions.get(m, '')}[/]")
        rows.append("")
        rows.append("[bold green]Done[/]")

        result_rows = rows
        win, sel_in_win, _ = _window(_menu_rows(result_rows, selected), selected)
        body = Table.grid(padding=(0, 1))
        body.add_column()
        for r in win:
            body.add_row(r)
        panel = Panel(
            Group(body),
            title=f"[{STYLE_TITLE}]Gemini voice models — tried top to bottom[/]",
            box=box.ROUNDED,
            border_style="blue",
        )
        _clear(console)
        console.print(panel)
        console.print(_footer(("Space", "on/off"), ("u/d", "move up/down"),
                                   ("Enter", "done"), ("Esc", "cancel")), justify="center")

        key = get_key(key_source)
        if key is None:
            return  # stream ended
        if key == "up":
            selected = (selected - 1) % len(rows)
        elif key == "down":
            selected = (selected + 1) % len(rows)
        elif key in ("u", "shift-up"):
            i = selected
            if 0 < i < len(order):
                order[i], order[i - 1] = order[i - 1], order[i]
                selected -= 1
        elif key in ("d", "shift-down"):
            i = selected
            if i < len(order) - 1:
                order[i], order[i + 1] = order[i + 1], order[i]
                selected += 1
        elif key == "space":
            i = selected
            if i < len(order):
                m = order[i]
                if m in settings["gemini_models"]:
                    if len(settings["gemini_models"]) > 1:
                        settings["gemini_models"].remove(m)
                else:
                    settings["gemini_models"].append(m)
        elif key == "enter":
            selected_models = [m for m in order if m in settings["gemini_models"]]
            if selected_models:
                settings["gemini_models"] = selected_models
                return
            # no selection: refuse to leave with nothing
        elif key == "escape":
            return


def _manager_view(console, key_source):
    """Browse/delete downloaded models. Tab switches group."""
    tab = 0  # 0 vosk, 1 whisper
    while True:
        entries = (models_manager.list_vosk_models() if tab == 0
                   else models_manager.list_whisper_models())
        location = (models_manager.VOSK_DIR if tab == 0 else models_manager.HF_HUB_DIR)
        rows = []
        for name, path, size in entries:
            rows.append(f"{name}  [dim]~{size} MB[/]")
        if not rows:
            rows.append("[dim](nothing downloaded)[/]")
        rows.append("")
        rows.append("[bold green]Back[/]")
        selected = 0

        while True:
            win, _, _ = _window(_menu_rows(rows, selected), selected)
            body = Table.grid(padding=(0, 1))
            body.add_column()
            for r in win:
                body.add_row(r)
            header = Table.grid(padding=(0, 1))
            header.add_column()
            vosk_title = "[bold cyan]Vosk[/]" if tab == 0 else "Vosk"
            whisper_title = "[bold cyan]Whisper (HF cache)[/]" if tab == 1 else "Whisper (HF cache)"
            header.add_row(f"{vosk_title}   {whisper_title}")
            header.add_row(Text(f"location: {location}", style="dim"))
            header.add_row(Rule(style="dim"))
            panel = Panel(
                Group(header, body),
                title=f"[{STYLE_TITLE}]Downloaded models[/]",
                box=box.ROUNDED,
                border_style="blue",
            )
            _clear(console)
            console.print(panel)
            console.print(_footer(("Tab", "switch group"), ("d", "delete"),
                                       ("Enter", "select"), ("Esc", "back")), justify="center")

            key = get_key(key_source)
            if key is None:
                return  # stream ended
            if key == "tab":
                tab = 1 - tab
                break
            if key == "up":
                selected = (selected - 1) % len(rows)
            elif key == "down":
                selected = (selected + 1) % len(rows)
            elif key == "d":
                if entries and selected < len(entries):
                    name, path, size = entries[selected]
                    confirm_rows = ["[bold]No, keep it[/]",
                                    f"[bold red]Yes, delete {name} (~{size} MB)[/]"]
                    confirm = _pick_list(console, key_source, "Delete model?", confirm_rows)
                    if confirm == 1:
                        models_manager._delete(path)
                    break  # refresh list
            elif key in ("enter", "escape"):
                if key == "enter" and selected == len(rows) - 1:
                    return
                if key == "escape":
                    return
            elif key in ("q", "ctrl-c", "ctrl-d"):
                raise SystemExit(0)


################################################################################################
# MAIN LOOP
################################################################################################

def run_tui(settings, on_test=None, console=None, key_source=None):
    """Interactive configuration session. Mutates settings; returns them on Start."""
    console = console or Console(highlight=False)
    if key_source is None:
        key_source = RealKeySource()

    unsaved = False
    selected = 0

    while True:
        left, items = _home_view(console, settings, unsaved)
        rows = _menu_rows(items, selected)
        right = Table.grid(padding=(0, 1))
        right.add_column()
        for r in rows:
            right.add_row(r)

        layout = Table.grid(padding=(1, 2))
        layout.add_column()
        layout.add_row(Panel(left, title="[bold]Current setup[/]",
                             box=box.SIMPLE_HEAVY, border_style="blue"))
        layout.add_row(Panel(right, title=f"[{STYLE_TITLE}]Main menu[/]",
                             box=box.ROUNDED, border_style="cyan"))

        _clear(console)
        console.print(
            Panel(layout, title=f"[{STYLE_TITLE}]TALKER Mic — Configuration[/]",
                  box=box.DOUBLE, border_style="cyan"),
            width=min(console.width, 76),
        )
        console.print(_footer(("", "move"), ("Enter", "select"), ("s", "save"),
                                   ("q", "quit")), justify="center")
        key = get_key(key_source)
        if key is None:
            raise SystemExit(0)  # stream ended: quit cleanly
        if key == "up":
            selected = (selected - 1) % len(items)
        elif key == "down":
            selected = (selected + 1) % len(items)
        elif key == "s":
            from settings import save_settings
            save_settings(settings)
            unsaved = False
        elif key in ("q", "ctrl-c", "ctrl-d"):
            print("Exiting without starting the microphone service.")
            raise SystemExit(0)
        elif key == "enter":
            action = HOME_ACTIONS[selected]
            if action == "start":
                return settings
            elif action == "save":
                from settings import save_settings
                save_settings(settings)
                unsaved = False
            elif action == "test":
                if on_test is not None:
                    _clear(console)
                    try:
                        on_test(settings)
                    except KeyboardInterrupt:
                        print("\nTest interrupted.")
                    except Exception as e:
                        print(f"Test failed: {e}")
                    input("\nPress Enter to return to the menu...")
            elif action == "provider":
                from settings import PROVIDERS
                prov_rows = [_provider_label(k, d) for k, d in PROVIDERS.items()]
                result = _pick_list(console, key_source, "Transcription provider", prov_rows)
                if result is not None:
                    settings["provider"] = list(PROVIDERS)[result]
                    unsaved = True
            elif action == "language":
                if _language_picker(console, key_source, settings):
                    unsaved = True
            elif action == "whisper":
                _whisper_picker(console, key_source, settings)
                unsaved = True
            elif action == "gemini":
                _gemini_picker(console, key_source, settings)
                unsaved = True
            elif action == "manager":
                _manager_view(console, key_source)
            elif action == "exit":
                print("Exiting without starting the microphone service.")
                raise SystemExit(0)
            # after any submenu, land back on Start for a quick launch
            selected = 0