# tui.py
# Textual-based TUI for the TALKER mic app - the "zone comms console"
# arrow keys AND mouse, clickable everything, live test pane with Stop
# (the classic prompt_toolkit TUI lives on as tui_old.py / talker_mic_old.exe)

import threading

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button, ContentSwitcher, Footer, Header, Input, Label, OptionList, RichLog, Static, Tree,
)
from textual.widgets.option_list import Option

from languages import (LANGUAGES, language_display_order, vosk_model_options,
                       vosk_model_info, whisper_supported, VOSK_BIG_MB)
import models_manager
from settings import (GEMINI_VOICE_MODES as GEMINI_MODELS_CANDIDATES, PROVIDERS,
                      WHISPER_MODELS, save_settings)

# ---------------------------------------------------------------- theme
BG = "#0a0e0a"
CHROME = "#101710"
PANEL = "#0d130d"
BORDER = "#2c3a2c"
ACCENT = "#9dff57"          # radiation green
ACCENT_DIM = "#1d3316"
TEXT = "#d8e8d0"
MUTED = "#6b7d6b"
AMBER = "#ffb000"           # anomaly warning
BAD = "#ff5544"

VIEWS = [
    ("home", "HOME  ·  base"),
    ("test", "RADIO CHECK  ·  live test"),
    ("provider", "CHANNEL  ·  provider"),
    ("language", "TONGUE  ·  language"),
    ("whisper", "WHISPER  ·  model size"),
    ("gemini", "GEMINI  ·  fallback chain"),
    ("manager", "STASH  ·  model vault"),
]
VIEW_KEYS = [k for k, _ in VIEWS]

CSS = f"""
Screen {{
    background: {BG};
    color: {TEXT};
}}
Header {{
    background: {CHROME};
    color: {TEXT};
}}
Footer {{
    background: {CHROME};
}}
#sidebar {{
    width: 36;
    min-width: 30;
    background: {PANEL};
    border-right: solid {BORDER};
    padding: 1 1 0 1;
}}
#sidebar Label.title {{
    color: {ACCENT};
    text-style: bold;
    margin-bottom: 0;
}}
#sidebar Label.sub {{
    color: {MUTED};
    margin-bottom: 1;
}}
Tree {{
    background: transparent;
    color: {TEXT};
    scrollbar-size: 1 1;
}}
Tree:focus > .tree--cursor {{
    background: {ACCENT_DIM};
    color: {TEXT};
    text-style: bold;
}}
.tree--cursor {{
    background: #16211a;
}}
.tree--guides {{
    color: {BORDER};
}}
#setup-strip, #cache-strip {{
    color: {MUTED};
    margin-top: 1;
}}
#contentwrap {{
    padding: 1 2 0 2;
}}
ContentSwitcher {{
    height: 1fr;
}}
.pane {{ height: 1fr; }}
Static.hint, Label.hint {{ color: {MUTED}; margin-bottom: 1; }}
.logbox {{
    border: round {BORDER};
    padding: 1;
    height: 1fr;
    color: {TEXT};
}}
Input, OptionList {{
    border: solid {BORDER};
    margin-bottom: 1;
}}
Input:focus, OptionList:focus {{ border: solid {ACCENT}; }}
Button {{
    margin-right: 1;
    margin-bottom: 1;
}}
Button.-primary {{ border: solid {ACCENT}; }}
Button.-warning {{ border: solid {AMBER}; }}
Button.-error {{ border: solid {BAD}; }}
ModalScreen {{
    align: center middle;
    background: {BG} 85%;
}}
#modal-box, .modalbox {{
    width: 60%;
    max-width: 80;
    background: {PANEL};
    border: solid {ACCENT};
    padding: 1 2;
}}
HelpBody {{ color: {TEXT}; }}
"""

HOME_INTRO = (
    "The Zone listens. Configure your rig, then go live.\n"
    "Settings stash themselves when you start the service."
)


def _lang_tag(code):
    info = vosk_model_info(code)
    if info:
        tag = f"vosk ~{info[1]}MB"
        if info[1] >= VOSK_BIG_MB:
            tag += " BIG"
        if len(vosk_model_options(code)) > 1:
            tag += f",{len(vosk_model_options(code))} models"
    else:
        tag = "no vosk"
    return f"{tag} | {'whisper' if whisper_supported(code) else 'no whisper'}"


# ---------------------------------------------------------------- modals
class HelpModal(ModalScreen):
    BINDINGS = [Binding("escape,f1,q,enter", "close", "Close", show=False)]

    def compose(self) -> ComposeResult:
        rows = [
            ("mouse", "everything is clickable"),
            ("Up/Dn / wheel", "move"),
            ("Enter / click", "select"),
            ("1 - 7", "jump between panes"),
            ("s", "save settings"),
            ("/", "focus the language filter"),
            ("F1", "this help"),
            ("q", "quit"),
        ]
        t = Table.grid(padding=(0, 3))
        t.add_column(style=ACCENT, no_wrap=True)
        t.add_column(style=TEXT)
        for k, v in rows:
            t.add_row(k, v)
        body = Group(
            Text("Zone comms console", style=f"bold {TEXT}"),
            Text(" "),
            t,
            Text(" "),
            Text("Local models cache on disk; purge them in the STASH.", style=MUTED),
        )
        yield Static(Panel(body, title="[accent]HELP[/]", title_align="left",
                           border_style=ACCENT, box=box.ROUNDED), classes="modalbox")

    def action_close(self) -> None:
        self.dismiss(False)


class ConfirmModal(ModalScreen):
    BINDINGS = [Binding("escape", "no", "No", show=False),
                Binding("enter", "no", "No", show=False)]

    def __init__(self, question: str):
        super().__init__()
        self.question = question

    def compose(self) -> ComposeResult:
        with Vertical(classes="modalbox"):
            yield Static(self.question, classes="HelpBody")
            with Horizontal():
                yield Button("No, keep it", id="confirm-no")
                yield Button("Yes, delete", id="confirm-yes", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-yes")


class ModelPickModal(ModalScreen):
    """Choose between multiple vosk models for one language."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, code: str, options: list):
        super().__init__()
        self.code = code
        self.options = options

    def compose(self) -> ComposeResult:
        with Vertical(classes="modalbox"):
            yield Static(f"Vosk models for {LANGUAGES.get(self.code, self.code)}",
                         classes="HelpBody")
            yield OptionList(*[
                Option(f"{name}  (~{size} MB)" + ("  [latest]" if i == 0 else ""),
                       id=name)
                for i, (name, size) in enumerate(self.options)
            ], id="model-pick-list")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        data = getattr(event.option, "id", None)
        self.dismiss(data)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------- app
class MicApp(App):
    CSS = CSS
    TITLE = "TALKER MIC - Zone Comms"
    BINDINGS = [
        Binding("q", "quit_service", "Quit"),
        Binding("s", "save", "Save"),
        Binding("f1", "help", "Help", key_display="F1"),
        Binding("1", "goto_view('home')", show=False),
        Binding("2", "goto_view('test')", show=False),
        Binding("3", "goto_view('provider')", show=False),
        Binding("4", "goto_view('language')", show=False),
        Binding("5", "goto_view('whisper')", show=False),
        Binding("6", "goto_view('gemini')", show=False),
        Binding("7", "goto_view('manager')", show=False),
        Binding("/", "focus_filter", show=False),
    ]

    current_view = reactive("home")
    _test_stop = None  # threading.Event while a radio check runs

    def __init__(self, settings: dict, test_func=None):
        super().__init__()
        self.settings = settings
        self._test_func = test_func
        self._gem_order = []  # display order of gemini candidates
        self._mgr_focus = "vosk"  # which stash list is active

    # ---- layout ---------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="main"):
            with Vertical(id="sidebar"):
                yield Label("TALKER MIC", classes="title")
                yield Label("zone comms console", classes="sub")
                tree: Tree = Tree("Views", id="nav")
                for key, label in VIEWS:
                    tree.root.add(label, data=key)
                tree.root.expand()
                yield tree
                yield Static(self._setup_strip(), id="setup-strip")
                yield Static(self._cache_strip(), id="cache-strip")
            with Vertical(id="contentwrap"):
                with ContentSwitcher(id="content"):
                    with VerticalScroll(id="home", classes="pane"):
                        yield Static(self._home_body(), id="home-body")
                        with Horizontal():
                            yield Button("GO LIVE - start mic service",
                                         id="btn-start", variant="primary")
                            yield Button("Save settings", id="btn-save")
                    with Vertical(id="test", classes="pane"):
                        yield Label("Radio check - tests your mic + model with the "
                                    "current settings", classes="hint")
                        yield Label("Press Start, then speak. Recording stops after "
                                    "~2s of silence - or press Stop.", classes="hint")
                        yield RichLog(id="test-log", classes="logbox", wrap=True,
                                      markup=False, max_lines=500)
                        with Horizontal():
                            yield Button("Start radio check", id="test-start",
                                         variant="primary")
                            yield Button("Stop recording", id="test-stop",
                                         variant="warning", disabled=True)
                    with VerticalScroll(id="provider", classes="pane"):
                        yield Label("Comms channel - who transcribes your voice",
                                    classes="hint")
                        yield OptionList(*self._provider_options(), id="provider-list")
                    with Vertical(id="language", classes="pane"):
                        yield Label("Tongue - pinned first, type to filter",
                                    classes="hint")
                        yield Input(placeholder="filter languages...  (/ to focus)",
                                    id="lang-filter")
                        yield OptionList(*self._language_options(""), id="lang-list")
                    with VerticalScroll(id="whisper", classes="pane"):
                        yield Label("Whisper model size - heavier is NOT better",
                                    classes="hint")
                        yield OptionList(*self._whisper_options(), id="whisper-list")
                    with Vertical(id="gemini", classes="pane"):
                        yield Label("Gemini chain - tried top to bottom",
                                    classes="hint")
                        yield OptionList(*self._gemini_options(), id="gemini-list")
                        with Horizontal():
                            yield Button("Toggle on/off", id="gem-toggle")
                            yield Button("Move up", id="gem-up")
                            yield Button("Move down", id="gem-down")
                    with VerticalScroll(id="manager", classes="pane"):
                        yield Label("Stash - local models on disk", classes="hint")
                        yield Static("", id="mgr-location", classes="hint")
                        yield OptionList(*self._mgr_vosk_options(), id="mgr-vosk")
                        yield OptionList(*self._mgr_whisper_options(),
                                         id="mgr-whisper")
                        with Horizontal():
                            yield Button("Delete selected", id="mgr-delete",
                                         variant="error")
                            yield Button("Refresh", id="mgr-refresh")
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one("#nav", Tree)
        tree.root.expand()
        tree.cursor_line = 1
        self.query_one("#content", ContentSwitcher).current = "home"
        self._refresh_manager()

    # ---- sidebar strips --------------------------------------------------
    def _setup_strip(self) -> Text:
        s = self.settings
        lines = [f"{s['provider'].replace('_', ' ')}  ·  "
                 f"{LANGUAGES.get(s['language'], s['language'])} ({s['language']})"]
        if s["provider"] == "whisper_local":
            lines.append(f"whisper {s['whisper_model']}")
        if s["provider"] == "gemini_proxy":
            lines.append(" -> ".join(m.split("/")[-1] for m in s["gemini_models"]))
        override = (s.get("vosk_model_overrides") or {}).get(s["language"])
        if override:
            lines.append(f"vosk: {override}")
        return Text("\n".join(lines), style=MUTED)

    def _cache_strip(self) -> Text:
        vosk = len(models_manager.list_vosk_models())
        whisper = len(models_manager.list_whisper_models())
        total = sum(e[2] for e in models_manager.list_vosk_models()) + \
            sum(e[2] for e in models_manager.list_whisper_models())
        return Text(f"stash: {vosk} vosk / {whisper} whisper  ~{total} MB", style=MUTED)

    def _refresh_strips(self) -> None:
        try:
            self.query_one("#setup-strip", Static).update(self._setup_strip())
            self.query_one("#cache-strip", Static).update(self._cache_strip())
        except Exception:
            pass

    # ---- pane bodies -----------------------------------------------------
    def _home_body(self):
        s = self.settings
        t = Table.grid(padding=(0, 2))
        t.add_column(style=MUTED, justify="right")
        t.add_column(style=TEXT)
        t.add_row("channel:", s["provider"].replace("_", " "))
        t.add_row("tongue:", f"{LANGUAGES.get(s['language'], s['language'])} ({s['language']})")
        if s["provider"] == "whisper_local":
            t.add_row("whisper:", s["whisper_model"])
        if s["provider"] == "gemini_proxy":
            t.add_row("chain:", "\n  ".join(m for m in s["gemini_models"]))
        override = (s.get("vosk_model_overrides") or {}).get(s["language"])
        if override:
            t.add_row("vosk:", override)
        return Panel(
            Group(Text(HOME_INTRO, style=MUTED), Text(" "), t),
            title=f"[{ACCENT}]RIG[/]", title_align="left",
            border_style=BORDER, box=box.ROUNDED,
        )

    def _provider_options(self):
        rows = []
        for key, desc in PROVIDERS.items():
            marker = " *" if key == self.settings["provider"] else ""
            rows.append(Option(f"{desc}{marker}", id=key))
        return rows

    def _language_options(self, query: str):
        q = query.lower()
        rows = []
        for code in language_display_order():
            if q and q not in LANGUAGES[code].lower() and q not in code:
                continue
            cur = " *" if code == self.settings["language"] else ""
            rows.append(Option(f"{LANGUAGES[code]} ({code})  {_lang_tag(code)}{cur}",
                               id=code))
        return rows or [Option("(no match)")]

    def _whisper_options(self):
        rows = []
        for name, desc in WHISPER_MODELS.items():
            cur = " *" if name == self.settings["whisper_model"] else ""
            rows.append(Option(f"{name}  {desc}{cur}", id=name))
        return rows

    def _gemini_options(self):
        candidates = [m for m, _ in GEMINI_MODELS_CANDIDATES]
        descriptions = dict(GEMINI_MODELS_CANDIDATES)
        self._gem_order = [m for m in self.settings["gemini_models"] if m in candidates]
        self._gem_order += [m for m in candidates if m not in self._gem_order]
        rows = []
        for i, m in enumerate(self._gem_order):
            on = m in self.settings["gemini_models"]
            mark = "[x]" if on else "[ ]"
            rows.append(Option(f"{i + 1}. {mark} {m}  - {descriptions.get(m, '')}",
                               id=m))
        return rows

    def _mgr_vosk_options(self):
        entries = models_manager.list_vosk_models()
        if not entries:
            return [Option("(nothing downloaded)")]
        return [Option(f"{name}  ~{size} MB", id=str(path))
                for name, path, size in entries]

    def _mgr_whisper_options(self):
        entries = models_manager.list_whisper_models()
        if not entries:
            return [Option("(nothing downloaded)")]
        return [Option(f"{name}  ~{size} MB", id=str(path))
                for name, path, size in entries]

    def _refresh_manager(self) -> None:
        try:
            vosk_list = self.query_one("#mgr-vosk", OptionList)
            vosk_list.clear_options()
            vosk_list.add_options(self._mgr_vosk_options())
            whisper_list = self.query_one("#mgr-whisper", OptionList)
            whisper_list.clear_options()
            whisper_list.add_options(self._mgr_whisper_options())
            self.query_one("#mgr-location", Static).update(
                Text(f"vosk: {models_manager.VOSK_DIR}\n"
                     f"whisper: {models_manager.HF_HUB_DIR}", style=MUTED))
        except Exception:
            pass
        self._refresh_strips()

    # ---- navigation ------------------------------------------------------
    def _goto(self, view: str) -> None:
        self.current_view = view
        self.query_one("#content", ContentSwitcher).current = view
        self.query_one("#nav", Tree).cursor_line = VIEW_KEYS.index(view) + 1
        focus_map = {"provider": "#provider-list", "language": "#lang-filter",
                     "whisper": "#whisper-list", "gemini": "#gemini-list"}
        if view in focus_map:
            try:
                self.query_one(focus_map[view]).focus()
            except Exception:
                pass

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        key = event.node.data
        if key in VIEW_KEYS:
            self._goto(key)

    def action_goto_view(self, view: str) -> None:
        self._goto(view)

    def action_focus_filter(self) -> None:
        self._goto("language")
        self.query_one("#lang-filter", Input).focus()

    def action_help(self) -> None:
        self.push_screen(HelpModal())

    def action_save(self) -> None:
        save_settings(self.settings)
        try:
            self.notify("settings stashed", title="saved")
        except Exception:
            pass
        self._refresh_strips()

    def action_quit_service(self) -> None:
        self.exit(None)

    # ---- home ------------------------------------------------------------
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        if btn == "btn-start":
            self.action_start()
        elif btn == "btn-save":
            self.action_save()
        elif btn == "gem-toggle":
            self._gem_toggle()
        elif btn == "gem-up":
            self._gem_move(-1)
        elif btn == "gem-down":
            self._gem_move(1)
        elif btn == "mgr-delete":
            self._mgr_delete()
        elif btn == "mgr-refresh":
            self._refresh_manager()
        elif btn == "test-start":
            self._start_test()
        elif btn == "test-stop":
            if self._test_stop is not None:
                self._test_stop.set()

    def action_start(self) -> None:
        # auto-stash on go-live (Q1): next launch remembers this setup
        save_settings(self.settings)
        self.exit(self.settings)

    # ---- option events ----------------------------------------------------
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        data = getattr(event.option, "id", None)
        if data is None:
            return
        ol = event.option_list
        if ol.id == "provider-list":
            if data in PROVIDERS:
                self.settings["provider"] = data
                self._refresh_strips()
                self._refresh_home()
                try:
                    self.notify(f"channel: {data}", title="provider")
                except Exception:
                    pass
        elif ol.id == "lang-list":
            self._select_language(data)
        elif ol.id == "whisper-list":
            self.settings["whisper_model"] = data
            self._refresh_strips()
            self._refresh_home()
        elif ol.id == "mgr-vosk":
            self._mgr_focus = "vosk"
        elif ol.id == "mgr-whisper":
            self._mgr_focus = "whisper"

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "lang-filter":
            lang_list = self.query_one("#lang-list", OptionList)
            lang_list.clear_options()
            lang_list.add_options(self._language_options(event.value))

    def _select_language(self, code: str) -> None:
        self.settings["language"] = code
        options = vosk_model_options(code)
        if len(options) > 1:
            self.push_screen(ModelPickModal(code, options),
                             lambda name: self._apply_model_choice(code, name))
        self._refresh_strips()
        self._refresh_home()
        try:
            self.notify(f"tongue: {LANGUAGES.get(code, code)}", title="language")
        except Exception:
            pass

    def _apply_model_choice(self, code: str, model_name) -> None:
        overrides = self.settings.setdefault("vosk_model_overrides", {})
        if model_name is None:
            return
        options = vosk_model_options(code)
        if model_name == options[0][0]:
            overrides.pop(code, None)
        else:
            overrides[code] = model_name
        self._refresh_strips()
        self._refresh_home()

    def _refresh_home(self) -> None:
        try:
            self.query_one("#home-body", Static).update(self._home_body())
        except Exception:
            pass

    # ---- gemini chain -----------------------------------------------------
    def _gem_highlighted(self):
        ol = self.query_one("#gemini-list", OptionList)
        idx = ol.highlighted
        if idx is None or not (0 <= idx < len(self._gem_order)):
            return None
        return idx

    def _gem_toggle(self) -> None:
        idx = self._gem_highlighted()
        if idx is None:
            return
        m = self._gem_order[idx]
        chain = self.settings["gemini_models"]
        if m in chain:
            if len(chain) > 1:
                chain.remove(m)
        else:
            chain.append(m)
        gem_list = self.query_one("#gemini-list", OptionList)
        gem_list.clear_options()
        gem_list.add_options(self._gemini_options())
        self._refresh_strips()
        self._refresh_home()

    def _gem_move(self, step: int) -> None:
        idx = self._gem_highlighted()
        if idx is None:
            return
        j = idx + step
        if 0 <= j < len(self._gem_order):
            self._gem_order[idx], self._gem_order[j] = self._gem_order[j], self._gem_order[idx]
            self.settings["gemini_models"] = [
                m for m in self._gem_order if m in self.settings["gemini_models"]]
            gem_list = self.query_one("#gemini-list", OptionList)
            gem_list.clear_options()
            gem_list.add_options(self._gemini_options())
            try:
                gem_list.highlighted = j
            except Exception:
                pass
        self._refresh_strips()
        self._refresh_home()

    # ---- stash / model manager ---------------------------------------------
    def _mgr_delete(self) -> None:
        ol_id = "#mgr-vosk" if self._mgr_focus == "vosk" else "#mgr-whisper"
        ol = self.query_one(ol_id, OptionList)
        idx = ol.highlighted
        entries = (models_manager.list_vosk_models() if self._mgr_focus == "vosk"
                   else models_manager.list_whisper_models())
        if idx is None or not (0 <= idx < len(entries)):
            try:
                self.notify("nothing selected", severity="warning")
            except Exception:
                pass
            return
        name, path, size = entries[idx]

        def _confirmed(confirmed: bool):
            if confirmed:
                models_manager._delete(path)
                self._refresh_manager()

        self.push_screen(ConfirmModal(f"Delete {name} (~{size} MB)?"), _confirmed)

    # ---- radio check (live test) --------------------------------------------
    def _test_log(self, msg: str) -> None:
        try:
            self.query_one("#test-log", RichLog).write(msg)
        except Exception:
            pass

    def _set_test_running(self, running: bool) -> None:
        try:
            self.query_one("#test-start", Button).disabled = running
            self.query_one("#test-stop", Button).disabled = not running
        except Exception:
            pass

    def _start_test(self) -> None:
        if self._test_func is None:
            self._test_log("[WARN] test function unavailable")
            return
        self._test_stop = threading.Event()
        self._set_test_running(True)
        self._test_log(f"--- radio check: {self.settings['provider']} "
                       f"({self.settings['language']}) ---")
        self._run_test_worker()

    @work(thread=True, group="test", exclusive=True)
    def _run_test_worker(self) -> None:
        stop = self._test_stop
        test_func = self._test_func
        settings = self.settings
        try:
            test_func(settings, status=lambda m: self.call_from_thread(self._test_log, m),
                      stop_requested=(lambda: stop.is_set()) if stop else None)
        except Exception as e:
            self.call_from_thread(self._test_log, f"[ERROR] {e}")
        finally:
            self.call_from_thread(self._set_test_running, False)
            self.call_from_thread(self._refresh_strips)


def run_tui(settings, on_test=None, **_kwargs):
    """Run the Textual zone-comms console. Returns settings on GO LIVE.

    Raises SystemExit(0) when the user quits without starting.
    """
    app = MicApp(settings, test_func=on_test)
    result = app.run()
    if result is None:
        print("Exiting without starting the microphone service.")
        raise SystemExit(0)
    return result