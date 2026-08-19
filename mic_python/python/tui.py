# tui.py
# Textual TUI for the TALKER mic app, styled after the in-game PDA:
# green-on-dark LCD, flat numbered menu, status dots, dashboard home,
# collapsible diagnostics log, radio check with REC indicator.

import inspect
import logging
import threading
from collections import deque

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
    Button, ContentSwitcher, Footer, Header, Input, Label, ListItem, ListView,
    OptionList, ProgressBar, RichLog, Static, Tree,
)
from textual.widgets.option_list import Option

from languages import (LANGUAGES, language_display_order, vosk_model_options,
                       vosk_model_info, vosk_model_by_name, whisper_supported, VOSK_BIG_MB)
import models_manager
from settings import (GEMINI_VOICE_MODES as GEMINI_MODELS_CANDIDATES, PROVIDERS,
                      WHISPER_MODELS, save_settings)

# ---------------------------------------------------------------- theme (PDA LCD)
BG = "#060a06"
CHROME = "#0c120c"
PANEL = "#0a100a"
BORDER = "#2a3a2a"
BORDER_DIM = "#1a241a"
ACCENT = "#8aff5a"          # LCD green
ACCENT_DIM = "#1d3316"
TEXT = "#cfe6c3"
MUTED = "#5f735f"
AMBER = "#ffb000"
BAD = "#ff5544"
RUST = "#c97b3d"            # worn metal accent

VIEWS = [
    ("home", "Home"),
    ("test", "Radio Check"),
    ("provider", "Provider"),
    ("language", "Language"),
    ("whisper", "Whisper Size"),
    ("gemini", "Gemini Chain"),
    ("custom", "Custom Models"),
    ("manager", "Model Manager"),
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
    border-bottom: solid {BORDER};
}}
Footer {{
    background: {CHROME};
}}
#main {{ height: 1fr; }}

/* ---------- sidebar: the PDA menu ---------- */
#sidebar {{
    width: 34;
    min-width: 28;
    background: {PANEL};
    border-right: solid {BORDER};
    padding: 1 1 0 1;
}}
#pda-title {{
    color: {ACCENT};
    text-style: bold;
    background: {ACCENT_DIM};
    padding: 0 1;
    width: auto;
}}
#pda-sub {{
    color: {MUTED};
    margin-bottom: 1;
}}
ListView {{
    background: transparent;
    padding: 0;
    height: auto;
    margin-bottom: 1;
}}
ListView > ListItem {{
    padding: 0 1;
    background: transparent;
}}
ListView > ListItem:hover {{
    background: {BORDER_DIM};
}}
ListView:focus > ListItem.-highlighted {{
    background: {ACCENT_DIM};
    text-style: bold;
}}
#setup-strip, #cache-strip {{
    color: {MUTED};
    margin-top: 1;
}}

/* ---------- content ---------- */
#contentwrap {{
    padding: 1 2 0 2;
}}
ContentSwitcher {{ height: 1fr; }}
.pane {{ height: 1fr; }}
Static.hint, Label.hint {{ color: {MUTED}; margin-bottom: 1; }}
.pane-title {{
    color: {ACCENT};
    text-style: bold;
    border-bottom: solid {BORDER};
    padding-bottom: 0;
    margin-bottom: 1;
}}

/* ---------- dashboard ---------- */
#dash-cards {{ height: auto; margin-bottom: 1; }}
Button.card {{
    width: 1fr;
    height: auto;
    min-height: 5;
    background: {PANEL};
    border: solid {BORDER};
    color: {TEXT};
    text-align: left;
    padding: 1 2;
    margin: 0 1 0 0;
}}
Button.card:hover {{ border: solid {ACCENT}; }}
Button.card .card-k {{
    color: {MUTED};
}}
#dash-actions {{ height: auto; margin-top: 1; }}
#btn-start {{
    background: {ACCENT_DIM};
    color: {ACCENT};
    text-style: bold;
    border: solid {ACCENT};
    min-width: 24;
    height: 3;
}}
#dash-note {{ color: {MUTED}; margin-top: 1; }}

/* ---------- radio check ---------- */
#test {{
    border: round {BORDER};
    padding: 0 1;
}}
#test.recording {{ border: round {BAD}; }}
#test-statusline {{ height: 1; margin-bottom: 1; }}
#rec-badge {{ width: 8; color: {MUTED}; }}
#rec-badge.on {{ color: {BAD}; text-style: bold; }}
#test-status {{ color: {MUTED}; }}
.logbox {{
    border: round {BORDER};
    padding: 1;
    height: 1fr;
    color: {TEXT};
}}
ProgressBar {{ margin-bottom: 1; grid-size: 1; }}

/* ---------- inputs & lists ---------- */
Input, OptionList {{
    border: solid {BORDER};
    margin-bottom: 1;
}}
Input:focus, OptionList:focus {{ border: solid {ACCENT}; }}

/* ---------- buttons ---------- */
Button {{ margin-right: 1; margin-bottom: 1; }}
Button.-primary {{ border: solid {ACCENT}; }}
Button.-warning {{ border: solid {AMBER}; }}
Button.-error {{ border: solid {BAD}; }}

/* ---------- proxy status lines ---------- */
.proxy-line {{ color: {MUTED}; margin-bottom: 1; }}
.proxy-line.ok {{ color: {ACCENT}; }}
.proxy-line.bad {{ color: {BAD}; }}

/* ---------- modals ---------- */
ModalScreen {{ align: center middle; background: {BG} 85%; }}
.modalbox {{
    width: 62%;
    max-width: 90;
    background: {PANEL};
    border: solid {ACCENT};
    padding: 1 2;
}}
HelpBody {{ color: {TEXT}; }}

/* ---------- diagnostics log pane ---------- */
#logpane {{
    height: 14;
    dock: bottom;
    border-top: solid {RUST};
    background: {BG};
    display: none;
    padding: 0 1;
}}
#logpane-label {{ color: {RUST}; width: auto; }}
#applog {{ border: none; height: 1fr; }}
"""


def _lang_tag(code, overrides=None):
    info = vosk_model_info(code)
    if info:
        tag = f"vosk ~{info[1]} MB"
        if info[1] >= VOSK_BIG_MB:
            tag += " BIG"
        if len(vosk_model_options(code)) > 1:
            tag += f",{len(vosk_model_options(code))} models"
        if overrides and overrides.get(code):
            tag += f" - {overrides[code]}"
    else:
        tag = "no vosk"
    return f"{tag} | {'whisper' if whisper_supported(code) else 'no whisper'}"


# ---------------------------------------------------------------- log capture
class _RingHandler(logging.Handler):
    """Feeds formatted log records into a deque drained by the TUI ticker."""

    def __init__(self, buffer: deque):
        super().__init__()
        self.buffer = buffer
        self.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                            datefmt="%H:%M:%S"))

    def emit(self, record):
        try:
            self.buffer.append((record.levelno, self.format(record)))
        except Exception:
            pass


# ---------------------------------------------------------------- modals
class HelpModal(ModalScreen):
    BINDINGS = [Binding("escape,f1,q,enter", "close", "Close", show=False)]

    def compose(self) -> ComposeResult:
        rows = [
            ("mouse", "everything is clickable"),
            ("1 - 8", "jump between screens"),
            ("Up/Dn / wheel", "move"),
            ("Enter / click", "select"),
            ("Esc", "back to Home"),
            ("s", "save settings"),
            ("/", "focus the language filter"),
            ("F12", "diagnostics log"),
            ("q", "quit"),
        ]
        t = Table.grid(padding=(0, 3))
        t.add_column(style=ACCENT, no_wrap=True)
        t.add_column(style=TEXT)
        for k, v in rows:
            t.add_row(k, v)
        body = Group(
            Text("TALKER PDA", style=f"bold {TEXT}"),
            Text(" "),
            t,
            Text(" "),
            Text("Local models cache on disk - manage them in Model Manager.", style=MUTED),
            Text("stalkers speak. the zone listens.", style=RUST),
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
        self.dismiss(getattr(event.option, "id", None))

    def action_cancel(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------- app
class MicApp(App):
    CSS = CSS
    TITLE = "TALKER PDA"
    SUB_TITLE = "zone comms"

    BINDINGS = [
        Binding("q", "quit_service", "Quit"),
        Binding("s", "save", "Save"),
        Binding("f1", "help", "Help", key_display="F1"),
        Binding("f12", "toggle_log", "Log", key_display="F12"),
        Binding("escape", "goto_view('home')", "Home", show=False),
        Binding("1", "goto_view('home')", show=False),
        Binding("2", "goto_view('test')", show=False),
        Binding("3", "goto_view('provider')", show=False),
        Binding("4", "goto_view('language')", show=False),
        Binding("5", "goto_view('whisper')", show=False),
        Binding("6", "goto_view('gemini')", show=False),
        Binding("7", "goto_view('custom')", show=False),
        Binding("8", "goto_view('manager')", show=False),
        Binding("/", "focus_filter", show=False),
    ]

    current_view = reactive("home")
    recording = reactive(False)
    _test_stop = None          # threading.Event while a radio check runs

    def __init__(self, settings: dict, test_func=None):
        super().__init__()
        self.settings = settings
        self._test_func = test_func
        self._gem_order = []            # display order of gemini candidates
        self._custom_order = []         # display order of custom models
        self._mgr_focus = "vosk"
        self._dirty = False
        self._rec_blink = True
        self._proxy_ok = None           # None = unknown, True/False after ping
        self._log_buf = deque(maxlen=500)
        self._log_handler = None

    # =======================================================================
    # LAYOUT
    # =======================================================================
    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="main"):
            with Vertical(id="sidebar"):
                yield Label("TALKER PDA", id="pda-title")
                yield Label("zone comms console", id="pda-sub")
                yield ListView(id="nav")
                yield Static(self._setup_strip(), id="setup-strip")
                yield Static(self._cache_strip(), id="cache-strip")
            with Vertical(id="contentwrap"):
                with ContentSwitcher(id="content"):
                    with VerticalScroll(id="home", classes="pane"):
                        yield Static(self._dash_header(), classes="pane-title",
                                     id="home-title")
                        yield Static(HOME_INTRO_TEXT, classes="hint", id="home-intro")
                        with Horizontal(id="dash-cards"):
                            yield Button(self._card_provider(), id="card-provider",
                                         classes="card")
                            yield Button(self._card_language(), id="card-language",
                                         classes="card")
                            yield Button(self._card_model(), id="card-model",
                                         classes="card")
                        with Horizontal(id="dash-actions"):
                            yield Button("GO LIVE - start mic service", id="btn-start",
                                         variant="primary")
                            yield Button("Save settings", id="btn-save")
                            yield Button("Radio check", id="btn-dash-test")
                        yield Static("On GO LIVE: settings are stashed and the selected "
                                     "model is prepared (downloads on first use).",
                                     id="dash-note")
                    with Vertical(id="test", classes="pane"):
                        yield Static("Radio Check - tests your mic + model with the "
                                     "current settings", classes="pane-title")
                        yield Label("Press Start, then speak. Recording stops after "
                                    "~2s of silence - or press Stop.", classes="hint")
                        with Horizontal(id="test-statusline"):
                            yield Static("o idle", id="rec-badge")
                            yield Static("", id="test-status")
                        yield RichLog(id="test-log", classes="logbox", wrap=True,
                                      markup=False, max_lines=500)
                        yield ProgressBar(id="test-progress", show_eta=False, total=100)
                        with Horizontal():
                            yield Button("Start radio check", id="test-start",
                                         variant="primary")
                            yield Button("Stop recording", id="test-stop",
                                         variant="warning", disabled=True)
                    with VerticalScroll(id="provider", classes="pane"):
                        yield Static("Provider - who transcribes your voice",
                                     classes="pane-title")
                        yield Label("Whisper is the recommended offline choice. Gemini "
                                    "and Custom need the API proxy running.",
                                    classes="hint")
                        yield OptionList(*self._provider_options(), id="provider-list")
                    with Vertical(id="language", classes="pane"):
                        yield Static("Language - pinned first, type to filter",
                                     classes="pane-title")
                        yield Input(placeholder="filter languages...  (/ to focus)",
                                    id="lang-filter")
                        yield OptionList(*self._language_options(""), id="lang-list")
                    with VerticalScroll(id="whisper", classes="pane"):
                        yield Static("Whisper Size", classes="pane-title")
                        yield Label("Cached models are marked and start instantly; "
                                    "others download once on first use.", classes="hint")
                        yield OptionList(*self._whisper_options(), id="whisper-list")
                    with Vertical(id="gemini", classes="pane"):
                        yield Static("Gemini Chain - tried top to bottom",
                                     classes="pane-title")
                        yield Label("Requires the API proxy with Gemini API key(s) "
                                    "configured.", classes="hint")
                        yield Static(self._proxy_line(), id="gemini-proxy-line",
                                     classes="proxy-line")
                        yield OptionList(*self._gemini_options(), id="gemini-list")
                        with Horizontal():
                            yield Button("Toggle on/off", id="gem-toggle")
                            yield Button("Move up", id="gem-up")
                            yield Button("Move down", id="gem-down")
                    with Vertical(id="custom", classes="pane"):
                        yield Static("Custom Models - your own fallback chain",
                                     classes="pane-title")
                        yield Label("Advanced: any audio-capable model on your proxy, "
                                    "format provider/modelname "
                                    "(e.g. gemini/gemini-3.5-flash-lite).",
                                    classes="hint")
                        yield Static(self._proxy_line(), id="custom-proxy-line",
                                     classes="proxy-line")
                        yield Input(placeholder="provider/modelname and press Enter",
                                    id="custom-input")
                        yield OptionList(*self._custom_options(), id="custom-list")
                        with Horizontal():
                            yield Button("Add", id="custom-add", variant="primary")
                            yield Button("Toggle on/off", id="custom-toggle")
                            yield Button("Move up", id="custom-up")
                            yield Button("Move down", id="custom-down")
                            yield Button("Delete", id="custom-delete", variant="error")
                    with VerticalScroll(id="manager", classes="pane"):
                        yield Static("Model Manager - local models on disk",
                                     classes="pane-title")
                        yield Static("", id="mgr-location", classes="hint")
                        yield OptionList(*self._mgr_vosk_options(), id="mgr-vosk")
                        yield OptionList(*self._mgr_whisper_options(), id="mgr-whisper")
                        with Horizontal():
                            yield Button("Delete selected", id="mgr-delete",
                                         variant="error")
                            yield Button("Refresh", id="mgr-refresh")
        with Vertical(id="logpane"):
            yield Label("DIAGNOSTICS - talker.log", id="logpane-label")
            yield RichLog(id="applog", markup=False, wrap=True, max_lines=500)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#content", ContentSwitcher).current = "home"
        self._refresh_nav()
        self._refresh_manager()
        # diagnostics capture
        self._log_handler = _RingHandler(self._log_buf)
        logging.getLogger().addHandler(self._log_handler)
        # periodic jobs
        self.set_interval(0.6, self._blink_rec)
        self.set_interval(0.5, self._drain_logs)
        self._ping_proxy()

    # =======================================================================
    # SIDEBAR / NAV
    # =======================================================================
    def _ready_map(self):
        p = self.settings["provider"]
        lang = self.settings["language"]
        ready = {k: True for k in VIEW_KEYS}
        # radio check readiness = current provider's model state
        if p == "whisper_local":
            size = self.settings["whisper_model"]
            ready["test"] = models_manager.whisper_model_cached(size)
        elif p == "vosk_local":
            name = (vosk_model_by_name(lang, (self.settings.get("vosk_model_overrides")
                                              or {}).get(lang, ""))
                    or vosk_model_info(lang) or (None,))[0]
            ready["test"] = bool(name and (models_manager.VOSK_DIR / name).is_dir())
        else:
            ready["test"] = bool(self._proxy_ok)
        ready["whisper"] = models_manager.whisper_model_cached(
            self.settings["whisper_model"])
        ready["gemini"] = bool(self._proxy_ok)
        ready["custom"] = bool(self._proxy_ok and self.settings.get("custom_models"))
        return ready

    def _refresh_nav(self) -> None:
        ready = self._ready_map()
        nav = self.query_one("#nav", ListView)
        index = nav.index
        nav.clear()
        for i, (key, label) in enumerate(VIEWS):
            dot = "[green]o[/]" if ready.get(key) else f"[{AMBER}]-[/]"
            marker = " <<" if key == self.current_view else ""
            nav.append(ListItem(Static(
                Text.assemble((f"{i + 1} ", "dim"), (label, ""), (marker, "bold")))))
        if index is not None and 0 <= index < len(VIEWS):
            nav.index = index
        self._refresh_strips()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.index is not None and 0 <= event.list_view.index < len(VIEWS):
            self._goto(VIEWS[event.list_view.index][0])

    def _goto(self, view: str) -> None:
        self.current_view = view
        self.query_one("#content", ContentSwitcher).current = view
        try:
            self.query_one("#nav", ListView).index = VIEW_KEYS.index(view)
        except Exception:
            pass
        focus_map = {"provider": "#provider-list", "language": "#lang-filter",
                     "whisper": "#whisper-list", "gemini": "#gemini-list",
                     "custom": "#custom-input"}
        if view in focus_map:
            try:
                self.query_one(focus_map[view]).focus()
            except Exception:
                pass

    def action_goto_view(self, view: str) -> None:
        self._goto(view)

    def action_focus_filter(self) -> None:
        self._goto("language")
        self.query_one("#lang-filter", Input).focus()

    def action_help(self) -> None:
        self.push_screen(HelpModal())

    # =======================================================================
    # PROXY REACHABILITY
    # =======================================================================
    @work(thread=True, group="ping", exclusive=True)
    def _ping_proxy(self) -> None:
        import proxy_common
        ok = proxy_common.check_proxy()
        self.call_from_thread(self._apply_proxy_ok, ok)

    def _apply_proxy_ok(self, ok: bool) -> None:
        self._proxy_ok = ok
        for sel in ("#gemini-proxy-line", "#custom-proxy-line"):
            try:
                line = self.query_one(sel, Static)
                line.update(self._proxy_line())
                line.set_class(ok, "ok")
                line.set_class(not ok, "bad")
            except Exception:
                pass
        self._refresh_nav()

    def _proxy_line(self) -> Text:
        if self._proxy_ok is None:
            return Text("? proxy: checking...")
        if self._proxy_ok:
            return Text("o proxy: reachable")
        return Text("x proxy: NOT reachable - start it and press r to recheck")

    # =======================================================================
    # SIDEBAR STRIPS / DASHBOARD
    # =======================================================================
    def _setup_strip(self) -> Text:
        s = self.settings
        lines = [f"{s['provider'].replace('_', ' ')}  ·  "
                 f"{LANGUAGES.get(s['language'], s['language'])} ({s['language']})"]
        if s["provider"] == "whisper_local":
            lines.append(f"whisper {s['whisper_model']}")
        if s["provider"] == "gemini_proxy":
            lines.append(" -> ".join(m.split("/")[-1] for m in s["gemini_models"]))
        if s["provider"] == "custom_proxy":
            lines.append(" -> ".join(s.get("custom_models") or []) or "(no models yet)")
        override = (s.get("vosk_model_overrides") or {}).get(s["language"])
        if override:
            lines.append(f"vosk: {override}")
        if self._dirty:
            lines.append("* unsaved changes")
        return Text("\n".join(lines), style=MUTED)

    def _cache_strip(self) -> Text:
        vosk = len(models_manager.list_vosk_models())
        whisper = len(models_manager.list_whisper_models())
        total = sum(e[2] for e in models_manager.list_vosk_models()) + \
            sum(e[2] for e in models_manager.list_whisper_models())
        return Text(f"on disk: {vosk} vosk / {whisper} whisper models, ~{total} MB",
                    style=MUTED)

    def _refresh_strips(self) -> None:
        try:
            self.query_one("#setup-strip", Static).update(self._setup_strip())
            self.query_one("#cache-strip", Static).update(self._cache_strip())
        except Exception:
            pass

    def _dash_header(self) -> str:
        return "TALKER PDA - HOME"

    def _card_provider(self) -> Text:
        p = self.settings["provider"]
        label = PROVIDERS.get(p, p).split(" - ")[0]
        return Text.assemble(("PROVIDER\n", "dim"), (label, "bold"))

    def _card_language(self) -> Text:
        code = self.settings["language"]
        return Text.assemble(("LANGUAGE\n", "dim"),
                             (f"{LANGUAGES.get(code, code)} ({code})", "bold"))

    def _card_model(self) -> Text:
        p = self.settings["provider"]
        if p == "whisper_local":
            size = self.settings["whisper_model"]
            cached = models_manager.whisper_model_cached(size)
            return Text.assemble(("MODEL\n", "dim"),
                                 (f"whisper {size}", "bold"),
                                 ("\ncached" if cached else "\nneeds download",
                                  "dim"))
        if p == "gemini_proxy":
            return Text.assemble(("MODEL\n", "dim"),
                                 (self.settings["gemini_models"][0].split("/")[-1],
                                  "bold"), (f"\n+{len(self.settings['gemini_models']) - 1} fallback(s)", "dim"))
        if p == "custom_proxy":
            n = len(self.settings.get("custom_models") or [])
            return Text.assemble(("MODEL\n", "dim"),
                                 (f"{n} custom model(s)" if n else "none yet", "bold"))
        name = (vosk_model_info(self.settings["language"]) or ("-",))[0]
        return Text.assemble(("MODEL\n", "dim"), (name, "bold"))

    def _refresh_dashboard(self) -> None:
        try:
            self.query_one("#card-provider", Button).label = self._card_provider()
            self.query_one("#card-language", Button).label = self._card_language()
            self.query_one("#card-model", Button).label = self._card_model()
        except Exception:
            pass
        self._refresh_nav()

    # =======================================================================
    # RECORDING INDICATOR
    # =======================================================================
    def watch_recording(self, recording: bool) -> None:
        try:
            pane = self.query_one("#test")
            badge = self.query_one("#rec-badge", Static)
            if recording:
                pane.add_class("recording")
                badge.add_class("on")
                badge.update("* REC")
                self.sub_title = "* REC"
            else:
                pane.remove_class("recording")
                badge.remove_class("on")
                badge.update("o idle")
                self.sub_title = "zone comms"
        except Exception:
            pass

    def _blink_rec(self) -> None:
        if not self.recording:
            return
        self._rec_blink = not self._rec_blink
        try:
            self.query_one("#rec-badge", Static).update(
                "* REC" if self._rec_blink else "  REC")
        except Exception:
            pass

    # =======================================================================
    # DIRTY TRACKING / SAVE / START
    # =======================================================================
    def _mark_dirty(self) -> None:
        self._dirty = True
        self._refresh_strips()

    def action_save(self) -> None:
        save_settings(self.settings)
        self._dirty = False
        self._refresh_strips()
        try:
            self.notify("settings stashed", title="saved")
        except Exception:
            pass

    def action_quit_service(self) -> None:
        self.exit(None)

    def action_start(self) -> None:
        if self.settings["provider"] == "custom_proxy" and \
                not self.settings.get("custom_models"):
            try:
                self.notify("add at least one custom model first "
                            "(provider/modelname)", severity="error",
                            title="no models")
            except Exception:
                pass
            self._goto("custom")
            return
        save_settings(self.settings)
        self.exit(self.settings)

    # =======================================================================
    # BUTTONS
    # =======================================================================
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        cards = {"card-provider": "provider", "card-language": "language"}
        model_target = {"whisper_local": "whisper", "gemini_proxy": "gemini",
                        "custom_proxy": "custom", "vosk_local": "whisper"}
        if btn in cards:
            self._goto(cards[btn])
        elif btn == "card-model":
            self._goto(model_target.get(self.settings["provider"], "whisper"))
        elif btn == "btn-start":
            self.action_start()
        elif btn == "btn-save":
            self.action_save()
        elif btn == "btn-dash-test":
            self._goto("test")
        elif btn == "gem-toggle":
            self._gem_toggle()
        elif btn == "gem-up":
            self._gem_move(-1)
        elif btn == "gem-down":
            self._gem_move(1)
        elif btn == "custom-add":
            self._custom_add()
        elif btn == "custom-toggle":
            self._custom_toggle()
        elif btn == "custom-up":
            self._custom_move(-1)
        elif btn == "custom-down":
            self._custom_move(1)
        elif btn == "custom-delete":
            self._custom_delete()
        elif btn == "mgr-delete":
            self._mgr_delete()
        elif btn == "mgr-refresh":
            self._refresh_manager()
        elif btn == "test-start":
            self._start_test()
        elif btn == "test-stop":
            if self._test_stop is not None:
                self._test_stop.set()

    # =======================================================================
    # OPTION LISTS
    # =======================================================================
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        data = getattr(event.option, "id", None)
        if data is None:
            return
        ol = event.option_list
        if ol.id == "provider-list":
            if data in PROVIDERS:
                self.settings["provider"] = data
                self._mark_dirty()
                self._refresh_strips()
                self._refresh_dashboard()
                try:
                    self.notify(f"provider: {data}", title="channel")
                except Exception:
                    pass
        elif ol.id == "lang-list":
            if data.startswith("lang:"):
                self._select_language(data[len("lang:"):])
        elif ol.id == "whisper-list":
            self.settings["whisper_model"] = data
            self._mark_dirty()
            self._refresh_strips()
            self._refresh_dashboard()
        elif ol.id == "mgr-vosk":
            self._mgr_focus = "vosk"
        elif ol.id == "mgr-whisper":
            self._mgr_focus = "whisper"

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "lang-filter":
            lang_list = self.query_one("#lang-list", OptionList)
            lang_list.clear_options()
            lang_list.add_options(self._language_options(event.value))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "custom-input":
            self._custom_add()

    # ---- provider pane
    def _provider_options(self):
        rows = []
        for key, desc in PROVIDERS.items():
            marker = "  *" if key == self.settings["provider"] else ""
            rows.append(Option(f"{desc}{marker}", id=key))
        return rows

    # ---- language pane
    def _language_options(self, query: str):
        q = query.lower()
        from settings import DEFAULT_SETTINGS
        pinned = ["en", "en-gb", "ru", "uk", "pl", "es"]

        def label_for(code):
            cur = "  *" if code == self.settings["language"] else ""
            return Option(f"{LANGUAGES[code]} ({code})  "
                          f"{_lang_tag(code, self.settings.get('vosk_model_overrides'))}{cur}",
                          id=f"lang:{code}")

        def header(text):
            return Option(f"-- {text} --", id=f"hdr:{text}")

        if q:
            matches = [c for c in language_display_order()
                       if q in LANGUAGES[c].lower() or q in c]
            return [label_for(c) for c in matches] or [Option("(no match)")]
        rows = [header("pinned")]
        rows += [label_for(c) for c in pinned]
        rows.append(header("all languages"))
        rows += [label_for(c) for c in language_display_order() if c not in pinned]
        return rows

    def _select_language(self, code: str) -> None:
        self.settings["language"] = code
        options = vosk_model_options(code)
        if len(options) > 1:
            self.push_screen(ModelPickModal(code, options),
                             lambda name: self._apply_model_choice(code, name))
        self._mark_dirty()
        self._refresh_strips()
        self._refresh_dashboard()
        try:
            self.notify(f"language: {LANGUAGES.get(code, code)}", title="set")
        except Exception:
            pass

    def _apply_model_choice(self, code: str, model_name) -> None:
        if model_name is None:
            return
        overrides = self.settings.setdefault("vosk_model_overrides", {})
        options = vosk_model_options(code)
        if model_name == options[0][0]:
            overrides.pop(code, None)
        else:
            overrides[code] = model_name
        self._mark_dirty()
        self._refresh_strips()
        self._refresh_dashboard()

    # ---- whisper pane
    def _whisper_options(self):
        rows = []
        for name, desc in WHISPER_MODELS.items():
            cur = "  *" if name == self.settings["whisper_model"] else ""
            cached = models_manager.whisper_model_cached(name)
            mark = " [cached]" if cached else ""
            style_prefix = "" if "NOT RECOMMENDED" not in desc else ""
            rows.append(Option(f"{name}  {desc}{mark}{cur}", id=name))
        return rows

    # ---- gemini pane
    def _gemini_options(self):
        candidates = [m for m, _ in GEMINI_MODELS_CANDIDATES]
        descriptions = dict(GEMINI_MODELS_CANDIDATES)
        self._gem_order = [m for m in self.settings["gemini_models"] if m in candidates]
        self._gem_order += [m for m in candidates if m not in self._gem_order]
        rows = []
        for i, m in enumerate(self._gem_order):
            on = m in self.settings["gemini_models"]
            check = "[x]" if on else "[ ]"
            rows.append(Option(f"{i + 1}. {check} {m}  - {descriptions.get(m, '')}",
                               id=m))
        return rows

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
        self._reload_list("#gemini-list", self._gemini_options())
        self._mark_dirty()
        self._refresh_dashboard()

    def _gem_move(self, step: int) -> None:
        idx = self._gem_highlighted()
        if idx is None:
            return
        j = idx + step
        if 0 <= j < len(self._gem_order):
            self._gem_order[idx], self._gem_order[j] = self._gem_order[j], self._gem_order[idx]
            self.settings["gemini_models"] = [
                m for m in self._gem_order if m in self.settings["gemini_models"]]
            self._reload_list("#gemini-list", self._gemini_options(), highlight=j)
        self._mark_dirty()
        self._refresh_dashboard()

    # ---- custom pane
    def _custom_options(self):
        chain = self.settings.get("custom_models") or []
        self._custom_order = list(chain)
        rows = []
        for i, m in enumerate(self._custom_order):
            rows.append(Option(f"{i + 1}. [x] {m}", id=m))
        if not rows:
            rows.append(Option("(no custom models - add one below)", id="empty"))
        return rows

    def _custom_add(self) -> None:
        try:
            entry = self.query_one("#custom-input", Input).value.strip()
        except Exception:
            return
        if not entry:
            return
        if "/" not in entry:
            try:
                self.notify("format must be provider/modelname "
                            "(e.g. gemini/gemini-3.5-flash-lite)",
                            severity="warning", title="bad format")
            except Exception:
                pass
            return
        chain = self.settings.setdefault("custom_models", [])
        if entry in chain:
            return
        chain.append(entry)
        try:
            self.query_one("#custom-input", Input).value = ""
        except Exception:
            pass
        self._reload_list("#custom-list", self._custom_options())
        self._mark_dirty()
        self._refresh_dashboard()
        try:
            self.notify(f"added {entry}", title="custom model")
        except Exception:
            pass

    def _custom_highlighted(self):
        ol = self.query_one("#custom-list", OptionList)
        idx = ol.highlighted
        if idx is None or not (0 <= idx < len(self._custom_order)):
            return None
        return idx

    def _custom_toggle(self) -> None:
        # custom chain entries are always on; toggle is remove (delete exists),
        # so this is a no-op kept for UI symmetry
        return

    def _custom_move(self, step: int) -> None:
        idx = self._custom_highlighted()
        if idx is None:
            return
        j = idx + step
        chain = self.settings.get("custom_models") or []
        if 0 <= j < len(chain):
            chain[idx], chain[j] = chain[j], chain[idx]
            self._reload_list("#custom-list", self._custom_options(), highlight=j)
            self._mark_dirty()
            self._refresh_dashboard()

    def _custom_delete(self) -> None:
        idx = self._custom_highlighted()
        if idx is None:
            return
        chain = self.settings.get("custom_models") or []
        if 0 <= idx < len(chain):
            removed = chain.pop(idx)
            self._reload_list("#custom-list", self._custom_options())
            self._mark_dirty()
            self._refresh_dashboard()
            try:
                self.notify(f"removed {removed}", title="custom model")
            except Exception:
                pass

    # ---- model manager
    def _mgr_vosk_options(self):
        entries = models_manager.list_vosk_models()
        if not entries:
            return [Option("(nothing downloaded)", id="empty")]
        return [Option(f"{name}  ~{size} MB", id=str(path))
                for name, path, size in entries]

    def _mgr_whisper_options(self):
        entries = models_manager.list_whisper_models()
        if not entries:
            return [Option("(nothing downloaded)", id="empty")]
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
        self._refresh_dashboard()

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

    # ---- helpers
    def _reload_list(self, selector: str, options, highlight=None):
        ol = self.query_one(selector, OptionList)
        ol.clear_options()
        ol.add_options(options)
        if highlight is not None:
            try:
                ol.highlighted = highlight
            except Exception:
                pass

    # =======================================================================
    # RADIO CHECK (LIVE TEST)
    # =======================================================================
    def _test_progress(self, message: str, current, total) -> None:
        try:
            bar = self.query_one("#test-progress", ProgressBar)
            status = self.query_one("#test-status", Static)
            if total and current is not None:
                bar.total = 100
                bar.progress = min(100, int(100 * current / total))
                status.update(f"{message}  {current}/{total} MB")
            elif "ready" in message or "cached" in message or "reachable" in message:
                bar.total = 100
                bar.progress = 100
                status.update(message)
            else:
                if bar.total is not None and bar.total != 0:
                    bar.total = None
                bar.advance(12)
                status.update(message)
        except Exception:
            pass

    def _test_log(self, msg: str) -> None:
        try:
            log = self.query_one("#test-log", RichLog)
            if msg.startswith("heard:"):
                log.write(Text(msg, style=f"bold {ACCENT}"))
            elif msg.startswith("[WARN]") or msg.startswith("[ERROR]"):
                log.write(Text(msg, style=BAD))
            else:
                log.write(msg)
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
        params = inspect.signature(test_func).parameters
        kwargs = {"status": lambda m: self.call_from_thread(self._test_log, m)}
        if "stop_requested" in params:
            kwargs["stop_requested"] = (lambda: stop.is_set()) if stop else None
        if "on_recording" in params:
            def _on_recording(active: bool):
                self.call_from_thread(setattr, self, "recording", active)
            kwargs["on_recording"] = _on_recording

        def _report(message, current, total):
            line = message + (f"  [{current}/{total} MB]" if total else "")
            self.call_from_thread(self._test_progress, message, current, total)
            self.call_from_thread(self._test_log, f"  {line}")

        try:
            import providers
            if not providers.prepare_model(settings, report=_report):
                self.call_from_thread(self._test_log,
                                      "[WARN] model/proxy not ready")
            test_func(settings, **kwargs)
        except TypeError:
            test_func(settings)
        except Exception as e:
            self.call_from_thread(self._test_log, f"[ERROR] {e}")
        finally:
            self.call_from_thread(self._set_test_running, False)
            self.call_from_thread(setattr, self, "recording", False)
            self.call_from_thread(self._refresh_dashboard)

    # =======================================================================
    # DIAGNOSTICS LOG PANE
    # =======================================================================
    def action_toggle_log(self) -> None:
        try:
            pane = self.query_one("#logpane")
            pane.display = not pane.display
        except Exception:
            pass

    def _drain_logs(self) -> None:
        if not self._log_buf:
            return
        records = []
        auto_open = False
        while self._log_buf:
            levelno, line = self._log_buf.popleft()
            records.append((levelno, line))
            if levelno >= logging.WARNING:
                auto_open = True
        try:
            log = self.query_one("#applog", RichLog)
            for levelno, line in records:
                style = BAD if levelno >= logging.ERROR else (
                    AMBER if levelno >= logging.WARNING else MUTED)
                log.write(Text(line, style=style))
            if auto_open:
                self.query_one("#logpane").display = True
        except Exception:
            pass


HOME_INTRO_TEXT = ("Configure your rig, then go live.\n"
                   "Everything is one click away - and the mouse works everywhere.")


def run_tui(settings, on_test=None, **_kwargs):
    """Run the PDA console. Returns settings on GO LIVE.

    Raises SystemExit(0) when the user quits without starting.
    """
    app = MicApp(settings, test_func=on_test)
    result = app.run()
    if result is None:
        print("Exiting without starting the microphone service.")
        raise SystemExit(0)
    return result
