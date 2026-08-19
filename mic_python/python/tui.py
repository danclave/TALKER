# tui.py
# Textual TUI for the TALKER mic app - "TALKER PDA v2"
# Everything the user can see was redesigned around the in-game PDA:
#   - custom status bar (device icons: mic, proxy signal, disk, clock)
#   - framed LCD screen with a flat numbered menu + readiness dots
#   - dashboard home with status cards and a hero GO LIVE
#   - Radio Check with a live audio level meter, silence countdown,
#     elapsed timer, big "heard" result panel and session history
#   - audio settings: microphone picker + silence threshold tuner
#   - first-run wizard, provider detail panel, per-size download button
#   - F12 diagnostics pane (auto-opens on warnings)

import inspect
import logging
import threading
from collections import deque
from datetime import datetime

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
from textual.screen import ModalScreen, Screen
from textual.timer import Timer
from textual.widgets import (
    Button, ContentSwitcher, Footer, Input, Label, ListItem, ListView,
    OptionList, ProgressBar, RichLog, Static,
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

INIT_STEPS = ["warming up the PDA", "importing audio engine",
              "scanning model cache", "listing microphones", "pinging the proxy"]

PINNED_LANGS = ["en", "en-gb", "ru", "uk", "pl", "es"]

CSS = f"""
Screen {{
    background: {BG};
    color: {TEXT};
}}

/* ============ status bar ============ */
#topbar {{
    height: 1;
    background: {CHROME};
    color: {TEXT};
    padding: 0 1;
}}
#topbar-left {{ width: auto; color: {ACCENT}; text-style: bold; }}
#topbar-mid {{ width: 1fr; content-align: center middle; color: {MUTED}; }}
#topbar-right {{ width: auto; color: {MUTED}; }}

/* ============ frame ============ */
#frame {{
    border: round {BORDER};
    padding: 0;
    margin: 0 1;
    height: 1fr;
}}
#main {{ height: 1fr; }}

/* ============ sidebar ============ */
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
.sidebar-section {{
    color: {BORDER};
    text-style: bold;
    margin-top: 1;
}}
ListView {{
    background: transparent;
    padding: 0;
    height: auto;
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
    border-left: solid {BORDER};
    padding-left: 1;
}}

/* ============ content ============ */
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
    margin-bottom: 1;
}}

/* ============ dashboard ============ */
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
#dash-actions {{ height: auto; margin-top: 1; }}
#btn-start {{
    background: {ACCENT_DIM};
    color: {ACCENT};
    text-style: bold;
    border: solid {ACCENT};
    min-width: 30;
    height: 3;
}}
#dash-note {{ color: {MUTED}; margin-top: 1; }}

/* ============ radio check ============ */
#test {{ border: none; padding: 0 1; }}
#test.recording {{ border: none; }}
#meter-row {{ height: 1; margin-bottom: 1; }}
#meter {{
    width: 1fr;
    color: {ACCENT};
    background: {BORDER_DIM};
}}
#meter-status {{ width: auto; color: {MUTED}; }}
#heard-panel {{
    border: round {BORDER};
    padding: 1 2;
    height: auto;
    min-height: 3;
    margin-bottom: 1;
}}
#heard-panel.filled {{ border: round {ACCENT}; }}
#history {{ color: {MUTED}; margin-bottom: 1; }}
.logbox {{
    border: round {BORDER};
    padding: 1;
    height: 1fr;
    color: {TEXT};
}}
ProgressBar {{ margin-bottom: 1; grid-size: 1; }}
#test-statusline {{ height: 1; margin-bottom: 1; }}
#rec-badge {{ width: 8; color: {MUTED}; }}
#rec-badge.on {{ color: {BAD}; text-style: bold; }}
#test-status {{ color: {MUTED}; }}

/* ============ audio settings ============ */
#audio-settings {{
    border: round {BORDER};
    padding: 1;
    margin-bottom: 1;
    height: auto;
}}
#audio-settings Label.section {{ color: {ACCENT}; text-style: bold; }}
#device-list {{ border: solid {BORDER}; margin-bottom: 1; }}
#thr-row {{ height: 3; }}
#thr-val {{ width: auto; color: {ACCENT}; text-style: bold; padding: 1 1; }}

/* ============ inputs & lists ============ */
Input, OptionList {{
    border: solid {BORDER};
    margin-bottom: 1;
}}
Input:focus, OptionList:focus {{ border: solid {ACCENT}; }}

/* ============ buttons ============ */
Button {{ margin-right: 1; margin-bottom: 1; }}
Button.-primary {{ border: solid {ACCENT}; }}
Button.-warning {{ border: solid {AMBER}; }}
Button.-error {{ border: solid {BAD}; }}
Button.small {{ height: 3; min-width: 8; }}

/* ============ provider detail ============ */
#provider-detail {{
    border: round {BORDER};
    padding: 1;
    margin-top: 1;
    color: {TEXT};
    height: auto;
    min-height: 6;
}}

/* ============ proxy lines ============ */
.proxy-line {{ color: {MUTED}; margin-bottom: 1; }}
.proxy-line.ok {{ color: {ACCENT}; }}
.proxy-line.bad {{ color: {BAD}; }}

/* ============ modals ============ */
ModalScreen {{ align: center middle; background: {BG} 85%; }}
.modalbox {{
    width: 64%;
    max-width: 92;
    background: {PANEL};
    border: solid {ACCENT};
    padding: 1 2;
}}
Wizard .modalbox {{
    width: 70%;
    height: 88%;
}}
.wizard-step {{ height: 1fr; }}
.wizard-step OptionList {{ height: 1fr; }}
HelpBody {{ color: {TEXT}; }}
.wizard-step {{ height: auto; }}

/* ============ diagnostics log pane ============ */
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

Footer {{ background: {CHROME}; }}
"""


def _lang_sort_key(code):
    """Order: whisper-supported languages first, vosk-only last."""
    return (0 if whisper_supported(code) else 1, LANGUAGES[code].lower())


def _language_codes():
    """pinned -> whisper-supported (alphabetical) -> vosk-only (alphabetical)."""
    rest = [c for c in language_display_order() if c not in PINNED_LANGS]
    rest.sort(key=_lang_sort_key)
    return list(PINNED_LANGS) + rest


def _lang_tag(code, overrides=None):
    """Compact engine tag. Sizes only for BIG vosk models."""
    has_vosk = vosk_model_info(code) is not None
    has_whisper = whisper_supported(code)
    if has_whisper and has_vosk:
        tag = "whisper + vosk"
    elif has_whisper:
        tag = "whisper"
    else:
        tag = "vosk only"
    info = vosk_model_info(code)
    if info and info[1] >= VOSK_BIG_MB:
        tag += f"  ~{info[1]} MB BIG"
    if overrides and overrides.get(code):
        tag += f" - {overrides[code]}"
    return tag


# ---------------------------------------------------------------- loading art
# 8-line block-letter TALKER; filled left-to-right, top-to-bottom
TALKER_ART = [
    "████████╗ █████╗ ██╗     ██╗  ██╗███████╗██████╗ ",
    "╚══██╔══╝██╔══██╗██║     ██║ ██╔╝██╔════╝██╔══██╗",
    "   ██║   ███████║██║     █████╔╝ █████╗  ██████╔╝",
    "   ██║   ██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗",
    "   ██║   ██║  ██║███████╗██║  ██╗███████╗██║  ██║",
    "   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝",
]

ART_WIDTH = max(len(line) for line in TALKER_ART)
ART_CELLS = sum(len(line) for line in TALKER_ART)


class LoadingScreen(ModalScreen):
    """Startup screen: TALKER ascii-art fills as init steps complete.

    Shown as the app's INITIAL screen (get_default_screen) so it is the
    first thing painted - no default-screen flash. The fill eases toward
    each completed step's target so it never stalls or teleports.
    """

    DEFAULT_CSS = """
    LoadingScreen { align: center middle; }
    #load-art { width: auto; }
    #load-step { color: #5f735f; margin-top: 1; }
    """

    target = reactive(0.0)
    _fill = 0.0   # eased value actually rendered

    def __init__(self, steps: list):
        super().__init__()
        self._steps = list(steps)
        self._done_steps = 0

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._render_art(), id="load-art")
            yield Static(self._step_text(), id="load-step")

    def on_mount(self) -> None:
        self.set_interval(0.07, self._ease_tick)

    def _ease_tick(self) -> None:
        if self._fill < self.target:
            # ease toward target; slower near the end so it never snaps
            remaining = self.target - self._fill
            step = max(0.004, remaining * 0.12)
            self._fill = min(self.target, self._fill + step)
            self._repaint()

    def _repaint(self) -> None:
        try:
            self.query_one("#load-art", Static).update(self._render_art(self._fill))
        except Exception:
            pass

    def _render_art(self, fraction: float = 0.0) -> Text:
        """Art with `fraction` of cells filled (dim -> LCD green)."""
        t = Text()
        remaining = int(fraction * ART_CELLS)
        for line in TALKER_ART:
            filled = max(0, min(len(line), remaining))
            t.append(line[:filled], style=ACCENT)
            t.append(line[filled:], style="#1a241a")
            t.append("\n")
            remaining -= filled
        return t

    def _step_text(self) -> str:
        if self._done_steps < len(self._steps):
            return f"{self._steps[self._done_steps]}..."
        return "ready."

    def advance(self, step_name: str = None) -> None:
        """One init step finished: raise the fill target and update label."""
        self._done_steps += 1
        self.target = min(1.0, self._done_steps / len(self._steps))
        try:
            self.query_one("#load-step", Static).update(self._step_text())
        except Exception:
            pass


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
            Text("Radio Check shows your live mic level and the silence "
                 "threshold - use it to debug auto-stop.", style=MUTED),
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


class Wizard(ModalScreen):
    """First-run setup, one step per view: Language -> Provider -> Confirm.

    Enter (or Next) advances; Back returns; Esc skips to the dashboard.
    """

    BINDINGS = [Binding("escape", "skip", "Skip", show=False),
                Binding("right", "next", "Next", show=False),
                Binding("left", "back", "Back", show=False)]

    STEP_TITLES = ["Language", "Provider", "Confirm"]

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self.step = 0
        self.picked_language = settings.get("language", "en")
        self.picked_provider = settings.get("provider", "whisper_local")

    def compose(self) -> ComposeResult:
        with Vertical(classes="modalbox wizard-box"):
            yield Static("First-time setup", id="wizard-title")
            yield Static("Esc skips to the dashboard anytime; you can change "
                         "everything later.", classes="HelpBody")
            with ContentSwitcher(id="wizard-content"):
                with Vertical(id="step-lang", classes="wizard-step"):
                    yield Static("What language will you speak?", classes="HelpBody")
                    yield Input(placeholder="filter... (pinned shown first)",
                                id="wizard-lang-filter")
                    yield OptionList(*self._lang_options(""),
                                     id="wizard-lang-list")
                with Vertical(id="step-provider", classes="wizard-step"):
                    yield Static("Who transcribes your voice?", classes="HelpBody")
                    yield OptionList(*self._provider_options(),
                                     id="wizard-provider-list")
                with Vertical(id="step-summary", classes="wizard-step"):
                    yield Static("", id="wizard-summary")
            with Horizontal():
                yield Button("Back", id="wizard-back", disabled=True)
                yield Button("Skip - use defaults", id="wizard-skip")
                yield Button("Next", id="wizard-next", variant="primary")

    def on_mount(self) -> None:
        self._set_step(0)

    # ---- option builders
    @staticmethod
    def _lang_options(query: str):
        q = query.lower()
        codes = _language_codes()
        if q:
            codes = [c for c in codes if q in LANGUAGES[c].lower() or q in c]
        return [Option(f"{LANGUAGES[c]} ({c})", id=f"lang:{c}") for c in codes[:40]] \
            or [Option("(no match)")]

    def _provider_options(self):
        return [Option(desc + ("  *" if key == self.picked_provider else ""), id=key)
                for key, desc in PROVIDERS.items()]

    # ---- step machinery
    def _set_step(self, i: int) -> None:
        i = max(0, min(2, i))
        self.step = i
        self.query_one("#wizard-content", ContentSwitcher).current = \
            ["step-lang", "step-provider", "step-summary"][i]
        self.query_one("#wizard-title", Static).update(
            f"First-time setup  -  step {i + 1} of 3: {self.STEP_TITLES[i]}")
        self.query_one("#wizard-back", Button).disabled = i == 0
        self.query_one("#wizard-next", Button).label = \
            "Finish" if i == 2 else "Next"
        if i == 0:
            try:
                ol = self.query_one("#wizard-lang-list", OptionList)
                self._highlight_language(ol)
            except Exception:
                pass
            self.query_one("#wizard-lang-filter", Input).focus()
        elif i == 1:
            ol = self.query_one("#wizard-provider-list", OptionList)
            ids = [(getattr(o, "id", "") or "") for o in ol._options]
            if self.picked_provider in ids:
                ol.highlighted = ids.index(self.picked_provider)
            ol.focus()
        else:
            self._render_summary()
            self.query_one("#wizard-next", Button).focus()

    def _highlight_language(self, ol: OptionList) -> None:
        ids = [(getattr(o, "id", "") or "") for o in ol._options]
        want = f"lang:{self.picked_language}"
        if want in ids:
            ol.highlighted = ids.index(want)

    def _render_summary(self) -> None:
        lang = f"{LANGUAGES.get(self.picked_language, self.picked_language)} " \
               f"({self.picked_language})"
        provider = PROVIDERS.get(self.picked_provider, self.picked_provider)
        self.query_one("#wizard-summary", Static).update(
            Text.assemble(("Your setup:\n\n", "bold"),
                          (f"Language  {lang}\n", TEXT),
                          (f"Provider  {provider}\n\n", TEXT),
                          ("Finish to stash these and open the dashboard - "
                           "run a Radio Check there to test your mic.",
                           "dim")))

    def _advance(self) -> None:
        # carry the highlighted choice even without Enter
        if self.step == 0:
            picked = self._highlighted_id("#wizard-lang-list")
            if picked and picked.startswith("lang:"):
                self.picked_language = picked[5:]
            self._set_step(1)
        elif self.step == 1:
            picked = self._highlighted_id("#wizard-provider-list")
            if picked in PROVIDERS:
                self.picked_provider = picked
            self._set_step(2)
        else:
            self.dismiss({"language": self.picked_language,
                          "provider": self.picked_provider})

    def _highlighted_id(self, selector: str):
        ol = self.query_one(selector, OptionList)
        idx = ol.highlighted
        ids = [(getattr(o, "id", "") or "") for o in ol._options]
        if idx is not None and 0 <= idx < len(ids):
            return ids[idx]
        return None

    # ---- events
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "wizard-lang-filter":
            ol = self.query_one("#wizard-lang-list", OptionList)
            ol.clear_options()
            ol.add_options(self._lang_options(event.value))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        data = getattr(event.option, "id", None)
        if event.option_list.id == "wizard-lang-list" and data \
                and data.startswith("lang:"):
            self.picked_language = data[5:]
            self._set_step(1)
        elif event.option_list.id == "wizard-provider-list" and data in PROVIDERS:
            self.picked_provider = data
            self._set_step(2)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "wizard-next":
            self._advance()
        elif event.button.id == "wizard-back":
            self._set_step(self.step - 1)
        elif event.button.id == "wizard-skip":
            self.dismiss(None)

    def action_skip(self) -> None:
        self.dismiss(None)

    def action_next(self) -> None:
        self._advance()

    def action_back(self) -> None:
        self._set_step(self.step - 1)


# modal meter: fixed absolute scale so the threshold marker is meaningful
MODAL_METER_MAX = 4000


class AudioSettingsModal(ModalScreen):
    """Microphone picker + silence threshold tuner with a LIVE level meter.

    The meter runs the whole time the modal is open (unless a radio check
    is recording) so you can watch how loud you are, flip microphones,
    and move the threshold to where speech clearly crosses it.
    """

    BINDINGS = [Binding("escape", "close", "Close", show=False)]

    def __init__(self, settings: dict, app_ref=None):
        super().__init__()
        self.settings = settings
        self._app = app_ref
        self._monitor = None          # recorder.LevelMonitor, lazy import
        self._display_level = 0.0

    def compose(self) -> ComposeResult:
        with Vertical(classes="modalbox"):
            yield Static("Audio settings", classes="HelpBody")
            yield Static("Microphone (applies immediately):", classes="HelpBody")
            yield OptionList(id="audio-devices")
            yield Static("LIVE INPUT - watch your level against the threshold",
                         classes="HelpBody")
            yield Static(self._meter_render(0.0), id="modal-meter")
            yield Static("", id="modal-meter-status")
            with Horizontal(id="thr-row"):
                yield Button("-", id="thr-down", classes="small")
                yield Static("", id="thr-val")
                yield Button("+", id="thr-up", classes="small")
            yield Static("Threshold = how loud input must be to count as "
                         "speech. The | marker on the meter IS the threshold - "
                         "bar left of it counts as silence.",
                         classes="HelpBody")
            yield Button("Done", id="audio-done", variant="primary")

    def on_mount(self) -> None:
        self._refresh()
        self.set_interval(1 / 15, self._meter_tick)
        self._ensure_monitor()
        app = self.app

        def _load():
            try:
                import sounddevice as sd
                devices = [(i, d["name"]) for i, d in enumerate(sd.query_devices())
                           if d.get("max_input_channels", 0) > 0]
            except Exception as e:
                logging.warning("Could not list input devices: %s", e)
                devices = []
            app.call_from_thread(self._apply_devices, devices)

        threading.Thread(target=_load, daemon=True).start()

    # ---- live monitor lifecycle
    def _ensure_monitor(self) -> None:
        if self._app is not None and self._app.recording:
            return  # never fight the radio check for the device
        if self._monitor is not None:
            return
        try:
            from recorder import LevelMonitor
            self._monitor = LevelMonitor(device=self.settings.get("input_device"))
            self._monitor.start()
        except Exception as e:
            logging.warning("live monitor unavailable: %s", e)
            self._monitor = None

    def _stop_monitor(self) -> None:
        if self._monitor is not None:
            self._monitor.stop()
            self._monitor = None

    def _meter_tick(self) -> None:
        level = self._monitor.get_level() if self._monitor else None
        if level is not None:
            self._display_level = level
        try:
            self.query_one("#modal-meter", Static).update(
                self._meter_render(self._display_level))
            threshold = int(self.settings.get("silence_level", 1000))
            speaking = self._display_level >= threshold
            status = self.query_one("#modal-meter-status", Static)
            if self._app is not None and self._app.recording:
                status.update(Text("paused - radio check is recording", style=MUTED))
            elif level is None and self._monitor is None:
                status.update(Text("monitor unavailable", style=MUTED))
            else:
                status.update(Text.assemble(
                    (f"level {int(self._display_level):4d}", TEXT),
                    (f"  threshold {threshold}", "dim"),
                    ("  SPEECH", ACCENT) if speaking else ("  silence", AMBER),
                ))
        except Exception:
            pass

    def _meter_render(self, level: float) -> Text:
        """20-cell bar on a fixed 0..MODAL_METER_MAX scale; threshold marker."""
        cells = int(round(20 * min(level, MODAL_METER_MAX) / MODAL_METER_MAX))
        threshold = int(self.settings.get("silence_level", 1000))
        thr_pos = int(round(20 * min(threshold, MODAL_METER_MAX) / MODAL_METER_MAX))
        bar = Text()
        filled_style = ACCENT if level >= threshold else AMBER
        for i in range(20):
            if i == thr_pos:
                bar.append("|", style=RUST)
            elif i < cells:
                bar.append("█", style=filled_style)
            else:
                bar.append("░", style="dim")
        if threshold >= MODAL_METER_MAX:
            bar.append(" |max", style=RUST)
        return bar

    def _apply_devices(self, devices) -> None:
        try:
            ol = self.query_one("#audio-devices", OptionList)
            ol.clear_options()
            current = self.settings.get("input_device")
            rows = [Option("Default microphone" +
                           ("  *" if current is None else ""), id="dev:none")]
            for idx, name in devices:
                marker = "  *" if current == idx else ""
                rows.append(Option(f"{idx}: {name}{marker}", id=f"dev:{idx}"))
            ol.add_options(rows)
        except Exception:
            pass

    def _refresh(self) -> None:
        try:
            self.query_one("#thr-val", Static).update(
                f"threshold {self.settings.get('silence_level', 1000)}")
        except Exception:
            pass

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        data = getattr(event.option, "id", None)
        if data == "dev:none":
            self.settings["input_device"] = None
        elif data and data.startswith("dev:"):
            try:
                self.settings["input_device"] = int(data[4:])
            except ValueError:
                return
        else:
            return
        # restart the live monitor on the new device
        self._stop_monitor()
        self._ensure_monitor()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "thr-down":
            current = int(self.settings.get("silence_level", 1000))
            self.settings["silence_level"] = max(100, current - 250)
            self._refresh()
        elif bid == "thr-up":
            current = int(self.settings.get("silence_level", 1000))
            self.settings["silence_level"] = min(8000, current + 250)
            self._refresh()
        elif bid == "audio-done":
            self._stop_monitor()
            self.dismiss(True)

    def action_close(self) -> None:
        self._stop_monitor()
        self.dismiss(True)

    def on_unmount(self) -> None:
        self._stop_monitor()


class ProviderPickModal(ModalScreen):
    """Pick a provider; closes on selection."""

    BINDINGS = [Binding("escape", "close", "Cancel", show=False)]

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings

    def compose(self) -> ComposeResult:
        with Vertical(classes="modalbox"):
            yield Static("Provider", classes="HelpBody")
            yield OptionList(*[
                Option(desc + ("  *" if key == self.settings["provider"] else ""),
                       id=key)
                for key, desc in PROVIDERS.items()
            ], id="pick-provider-list")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        data = getattr(event.option, "id", None)
        if data in PROVIDERS:
            self.dismiss(data)
        else:
            self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)


class LanguagePickModal(ModalScreen):
    """Searchable language picker; closes on selection."""

    BINDINGS = [Binding("escape", "close", "Cancel", show=False)]

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings

    def compose(self) -> ComposeResult:
        with Vertical(classes="modalbox"):
            yield Static("Language", classes="HelpBody")
            yield Input(placeholder="filter...", id="pick-lang-filter")
            yield OptionList(id="pick-lang-list")

    def on_mount(self) -> None:
        self._refresh("")

    def _refresh(self, query: str):
        q = query.lower()
        codes = _language_codes()
        if q:
            codes = [c for c in codes if q in LANGUAGES[c].lower() or q in c]
        rows = [Option(f"{LANGUAGES[c]} ({c})  "
                       f"{_lang_tag(c, self.settings.get('vosk_model_overrides'))}"
                       + ("  *" if c == self.settings["language"] else ""),
                       id=f"lang:{c}") for c in codes[:80]]
        try:
            ol = self.query_one("#pick-lang-list", OptionList)
            ol.clear_options()
            ol.add_options(rows or [Option("(no match)")])
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "pick-lang-filter":
            self._refresh(event.value)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        data = getattr(event.option, "id", None)
        if data and data.startswith("lang:"):
            self.dismiss(data[5:])
        else:
            self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)


class WhisperPickModal(ModalScreen):
    """Pick a whisper size; closes on selection."""

    BINDINGS = [Binding("escape", "close", "Cancel", show=False)]

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings

    def compose(self) -> ComposeResult:
        with Vertical(classes="modalbox"):
            yield Static("Whisper size", classes="HelpBody")
            yield OptionList(*[
                Option(f"{name}  {desc}"
                       + (" [cached]" if models_manager.whisper_model_cached(name) else "")
                       + ("  *" if name == self.settings["whisper_model"] else ""),
                       id=name)
                for name, desc in WHISPER_MODELS.items()
            ], id="pick-whisper-list")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(getattr(event.option, "id", None))

    def action_close(self) -> None:
        self.dismiss(None)


class VoskPickModal(ModalScreen):
    """Pick a vosk model for the current language; closes on selection."""

    BINDINGS = [Binding("escape", "close", "Cancel", show=False)]

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings

    def compose(self) -> ComposeResult:
        code = self.settings["language"]
        info = vosk_model_info(code)
        with Vertical(classes="modalbox"):
            yield Static(f"Vosk model for {LANGUAGES.get(code, code)}",
                         classes="HelpBody")
            yield OptionList(id="pick-vosk-list")

    def on_mount(self) -> None:
        code = self.settings["language"]
        options = vosk_model_options(code)
        override = (self.settings.get("vosk_model_overrides") or {}).get(code)
        rows = []
        for i, (name, size) in enumerate(options):
            label = f"{name}  (~{size} MB)"
            if i == 0:
                label += "  [latest]"
            if override == name or (i == 0 and not override):
                label += "  *"
            rows.append(Option(label, id=name))
        try:
            self.query_one("#pick-vosk-list", OptionList).add_options(rows)
        except Exception:
            pass

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(getattr(event.option, "id", None))

    def action_close(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------- app
class MicApp(App):
    CSS = CSS
    TITLE = "TALKER PDA"
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

    def __init__(self, settings: dict, test_func=None, wizard=False):
        super().__init__()
        self.settings = settings
        self._test_func = test_func
        self._gem_order = []
        self._custom_order = []
        self._mgr_focus = "vosk"
        self._dirty = False
        self._rec_blink = True
        self._proxy_ok = None
        self._log_buf = deque(maxlen=500)
        self._log_handler = None
        self._history = deque(maxlen=20)   # (time, provider, text, seconds)
        self._wizard = wizard
        self._devices = []                 # [(index, name)] input devices

    # =======================================================================
    # LAYOUT
    # =======================================================================
    def compose(self) -> ComposeResult:
        # main UI lives on the default screen; the loader is pushed on top
        yield from self.compose_ui()

    def compose_ui(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Static("TALKER PDA v2", id="topbar-left")
            yield Static("", id="topbar-mid")
            yield Static("", id="topbar-right")
        with Vertical(id="frame"):
            with Horizontal(id="main"):
                with Vertical(id="sidebar"):
                    yield Label("TALKER PDA", id="pda-title")
                    yield Label("zone comms console", id="pda-sub")
                    yield Label("NAVIGATION", classes="sidebar-section")
                    yield ListView(id="nav")
                    yield Static(self._setup_strip(), id="setup-strip")
                    yield Static(self._cache_strip(), id="cache-strip")
                with Vertical(id="contentwrap"):
                    with ContentSwitcher(id="content"):
                        with VerticalScroll(id="home", classes="pane"):
                            yield Static("Dashboard", classes="pane-title",
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
                                yield Button("GO LIVE - start mic service",
                                             id="btn-start", variant="primary")
                                yield Button("Save settings", id="btn-save")
                                yield Button("Radio check", id="btn-dash-test")
                            yield Static("On GO LIVE: settings are stashed and the "
                                         "selected model is prepared (downloads on "
                                         "first use).", id="dash-note")
                        with VerticalScroll(id="test", classes="pane"):
                            yield Static("Radio Check", classes="pane-title")
                            yield Label("Press Start, then speak. The meter shows "
                                        "your live mic level; recording stops when "
                                        "it stays left of the threshold mark.",
                                        classes="hint")
                            with Horizontal(id="test-statusline"):
                                yield Static("o idle", id="rec-badge")
                                yield Static("", id="test-status")
                            with Horizontal(id="meter-row"):
                                yield Static(self._meter_render(0), id="meter")
                                yield Static("0.0s", id="meter-status")
                            yield RichLog(id="test-log", classes="logbox", wrap=True,
                                          markup=False, max_lines=300)
                            yield ProgressBar(id="test-progress", show_eta=False,
                                              total=100)
                            yield Static(self._heard_render(None, None),
                                         id="heard-panel")
                            yield Static("", id="history")
                            with Horizontal():
                                yield Button("Start radio check", id="test-start",
                                             variant="primary")
                                yield Button("Stop recording", id="test-stop",
                                             variant="warning", disabled=True)
                                yield Button("Audio settings...", id="audio-open")
                        with VerticalScroll(id="provider", classes="pane"):
                            yield Static("Provider", classes="pane-title")
                            yield Label("Whisper is the recommended offline choice. "
                                        "Gemini and Custom need the API proxy "
                                        "running.", classes="hint")
                            yield OptionList(*self._provider_options(),
                                             id="provider-list")
                            yield Static(self._provider_detail(None),
                                         id="provider-detail")
                        with Vertical(id="language", classes="pane"):
                            yield Static("Language", classes="pane-title")
                            yield Label("Pinned first, then everything else. "
                                        "Whisper-capable languages come before "
                                        "vosk-only ones.", classes="hint")
                            yield Input(placeholder="filter languages...  (/ to focus)",
                                        id="lang-filter")
                            yield OptionList(*self._language_options(""),
                                             id="lang-list")
                        with VerticalScroll(id="whisper", classes="pane"):
                            yield Static("Whisper Size", classes="pane-title")
                            yield Label("Cached models start instantly; others "
                                        "download once.", classes="hint")
                            yield OptionList(*self._whisper_options(),
                                             id="whisper-list")
                            with Horizontal():
                                yield Button("Download / preload highlighted",
                                             id="whisper-download")
                        with Vertical(id="gemini", classes="pane"):
                            yield Static("Gemini Chain - tried top to bottom",
                                         classes="pane-title")
                            yield Label("Requires the API proxy with Gemini API "
                                        "key(s) configured.", classes="hint")
                            yield Static(self._proxy_line(), id="gemini-proxy-line",
                                         classes="proxy-line")
                            yield OptionList(*self._gemini_options(),
                                             id="gemini-list")
                            with Horizontal():
                                yield Button("Toggle on/off", id="gem-toggle")
                                yield Button("Move up", id="gem-up")
                                yield Button("Move down", id="gem-down")
                        with Vertical(id="custom", classes="pane"):
                            yield Static("Custom Models - your own fallback chain",
                                         classes="pane-title")
                            yield Label("Advanced: any audio-capable model on your "
                                        "proxy, format provider/modelname "
                                        "(e.g. gemini/gemini-3.5-flash-lite).",
                                        classes="hint")
                            yield Static(self._proxy_line(), id="custom-proxy-line",
                                         classes="proxy-line")
                            yield Input(placeholder="provider/modelname and press Enter",
                                        id="custom-input")
                            yield OptionList(*self._custom_options(),
                                             id="custom-list")
                            with Horizontal():
                                yield Button("Add", id="custom-add", variant="primary")
                                yield Button("Move up", id="custom-up")
                                yield Button("Move down", id="custom-down")
                                yield Button("Delete", id="custom-delete",
                                             variant="error")
                        with VerticalScroll(id="manager", classes="pane"):
                            yield Static("Model Manager - local models on disk",
                                         classes="pane-title")
                            yield Static("", id="mgr-location", classes="hint")
                            yield OptionList(*self._mgr_vosk_options(), id="mgr-vosk")
                            yield OptionList(*self._mgr_whisper_options(),
                                             id="mgr-whisper")
                            with Horizontal():
                                yield Button("Delete selected", id="mgr-delete",
                                             variant="error")
                                yield Button("Refresh", id="mgr-refresh")
        with Vertical(id="logpane"):
            yield Label("DIAGNOSTICS - talker.log", id="logpane-label")
            yield RichLog(id="applog", markup=False, wrap=True, max_lines=500)
        yield Footer()

    def on_mount(self) -> None:
        # main UI is composed on the default screen; set it up, then cover
        # it with the loader while real init work runs
        self._setup_main_ui()
        self._loader = LoadingScreen(INIT_STEPS)
        self.push_screen(self._loader)
        self._init_worker(self._loader)

    @work(thread=True, group="init", exclusive=True)
    def _init_worker(self, loader: LoadingScreen) -> None:
        from time import perf_counter as _pc
        t0 = _pc()

        def done(name: str):
            self.call_from_thread(loader.advance, name)

        logging.info("boot: init worker start")
        done("warming up")
        try:
            import numpy  # noqa: F401  (recorder pulls it anyway)
            import sounddevice  # noqa: F401  (the genuinely slow import)
            done("audio engine")
        except Exception as e:
            logging.error("boot: audio engine import failed: %s", e)
            done("audio engine")
        logging.info("boot: audio engine ready at %.2fs", _pc() - t0)
        models_manager.list_vosk_models()      # warms the disk scan
        models_manager.list_whisper_models()
        done("model cache")
        logging.info("boot: cache scan done at %.2fs", _pc() - t0)
        try:
            import sounddevice as sd
            sd.query_devices()
            done("microphones")
        except Exception:
            done("microphones")
        import proxy_common
        proxy_common.check_proxy()
        done("proxy")
        logging.info("boot: init complete at %.2fs - switching to app", _pc() - t0)

        # brief 100% hold, then swap the loading screen for the real UI
        import time as _time
        _time.sleep(0.25)
        self.call_from_thread(self._show_main_ui)

    def _show_main_ui(self) -> None:
        """Pop the loading screen; the main UI (default screen) is beneath."""
        try:
            self.pop_screen()
        except Exception as e:
            logging.error("boot: could not pop loading screen: %s", e)

    def _ui(self, selector, widget_type=None):
        """Query a widget on the base (main UI) screen, not the topmost
        modal/loader - handlers must keep working under any popup."""
        base = self.screen_stack[0] if self.screen_stack else None
        if base is None:
            from textual.css.query import NoMatches
            raise NoMatches("no screens mounted")
        if widget_type is not None:
            return base.query_one(selector, widget_type)
        return base.query_one(selector)

    def _setup_main_ui(self) -> None:
        """Configure the composed main UI on the default screen."""
        frame = self._ui("#frame")
        frame.border_title = "TALKER PDA"
        frame.border_subtitle = "v2"
        self._ui("#content", ContentSwitcher).current = "home"
        self._refresh_nav()
        self._refresh_manager()
        self._log_handler = _RingHandler(self._log_buf)
        logging.getLogger().addHandler(self._log_handler)
        self.set_interval(0.6, self._blink_rec)
        self.set_interval(0.5, self._drain_logs)
        self.set_interval(1.0, self._tick_clock)
        self._tick_clock()
        self._ping_proxy()
        self._list_devices()
        if self._wizard:
            self.push_screen(Wizard(self.settings), self._wizard_done)

    def _wizard_done(self, result):
        if result:
            if result.get("language"):
                self.settings["language"] = result["language"]
            if result.get("provider"):
                self.settings["provider"] = result["provider"]
            self._mark_dirty()
            self._refresh_dashboard()
            try:
                self.notify("setup applied - run a Radio Check to test",
                            title="welcome")
            except Exception:
                pass

    # =======================================================================
    # STATUS BAR
    # =======================================================================
    def _tick_clock(self) -> None:
        try:
            right = self._ui("#topbar-right", Static)
            disk_mb = (sum(e[2] for e in models_manager.list_vosk_models()) +
                       sum(e[2] for e in models_manager.list_whisper_models()))
            proxy_icon = "?" if self._proxy_ok is None else \
                ("|||" if self._proxy_ok else " x ")
            needed = self._proxy_needed()
            proxy_part = f" proxy {proxy_icon}" if needed else ""
            right.update(Text.assemble(
                ("mic ", "dim"),
                (self._mic_icon(), ACCENT if self._mic_ready() else AMBER),
                (proxy_part + "   disk ", "dim"),
                (f"~{disk_mb} MB", TEXT),
                ("   ", "dim"),
                (datetime.now().strftime("%H:%M"), TEXT),
            ))
            mid = self._ui("#topbar-mid", Static)
            p = self.settings["provider"]
            model = self._current_model_label()
            mid.update(f"{p.replace('_', ' ')}  |  {model}  |  "
                       f"{LANGUAGES.get(self.settings['language'], '')}")
        except Exception:
            pass

    def _mic_icon(self) -> str:
        return "O" if self._mic_ready() else "-"

    def _mic_ready(self) -> bool:
        return self._ready_map().get("test", False)

    def _proxy_needed(self) -> bool:
        return self.settings["provider"] in ("gemini_proxy", "custom_proxy")

    def _current_model_label(self) -> str:
        p = self.settings["provider"]
        if p == "whisper_local":
            return f"whisper {self.settings['whisper_model']}"
        if p == "gemini_proxy":
            return " -> ".join(m.split("/")[-1] for m in self.settings["gemini_models"])
        if p == "custom_proxy":
            n = len(self.settings.get("custom_models") or [])
            return f"{n} custom model(s)"
        info = vosk_model_info(self.settings["language"])
        return f"vosk {info[0]}" if info else "vosk"

    # =======================================================================
    # SIDEBAR / NAV
    # =======================================================================
    def _ready_map(self):
        p = self.settings["provider"]
        lang = self.settings["language"]
        ready = {k: True for k in VIEW_KEYS}
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
        nav = self._ui("#nav", ListView)
        index = nav.index
        nav.clear()
        for i, (key, label) in enumerate(VIEWS):
            ok = ready.get(key)
            row = Text.assemble(
                (f"{i + 1} ", "dim"),
                ("O", ACCENT if ok else "dim"),
                (" ", ""),
                ("-", AMBER) if not ok else (" ", ""),
                (label, ""),
            ) if not ok else Text.assemble(
                (f"{i + 1} ", "dim"),
                ("O ", ACCENT),
                (label, ""),
            )
            nav.append(ListItem(Static(row)))
        if index is None or not (0 <= index < len(VIEWS)):
            index = VIEW_KEYS.index(self.current_view)
        nav.index = index
        self._refresh_strips()
        self._tick_clock()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.index is not None and 0 <= event.list_view.index < len(VIEWS):
            self._goto(VIEWS[event.list_view.index][0])

    def _goto(self, view: str) -> None:
        self.current_view = view
        self._ui("#content", ContentSwitcher).current = view
        try:
            self._ui("#nav", ListView).index = VIEW_KEYS.index(view)
        except Exception:
            pass
        focus_map = {"provider": "#provider-list", "language": "#lang-filter",
                     "whisper": "#whisper-list", "gemini": "#gemini-list",
                     "custom": "#custom-input"}
        if view in focus_map:
            try:
                self._ui(focus_map[view]).focus()
            except Exception:
                pass

    def action_goto_view(self, view: str) -> None:
        self._goto(view)

    def action_focus_filter(self) -> None:
        self._goto("language")
        self._ui("#lang-filter", Input).focus()

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
                line = self._ui(sel, Static)
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
            return Text("O proxy: reachable")
        return Text("x proxy: NOT reachable - start it, then Refresh in Model Manager")

    # =======================================================================
    # DEVICE PICKER (populated inside AudioSettingsModal; kept here for
    # potential status display)
    # =======================================================================
    @work(thread=True, group="devices", exclusive=True)
    def _list_devices(self) -> None:
        try:
            import sounddevice as sd
            devices = [(i, d["name"]) for i, d in enumerate(sd.query_devices())
                       if d.get("max_input_channels", 0) > 0]
        except Exception as e:
            logging.warning("Could not list input devices: %s", e)
            devices = []
        self._devices = devices

    # =======================================================================
    # SIDEBAR STRIPS / DASHBOARD
    # =======================================================================
    def _setup_strip(self) -> Text:
        s = self.settings
        lines = [f"{s['provider'].replace('_', ' ')}  ·  "
                 f"{LANGUAGES.get(s['language'], s['language'])} ({s['language']})"]
        lines.append(self._current_model_label())
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
        return Text(f"on disk: {vosk} vosk / {whisper} whisper, ~{total} MB",
                    style=MUTED)

    def _refresh_strips(self) -> None:
        try:
            self._ui("#setup-strip", Static).update(self._setup_strip())
            self._ui("#cache-strip", Static).update(self._cache_strip())
        except Exception:
            pass

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
                                  "bold"),
                                 (f"\n+{len(self.settings['gemini_models']) - 1} fallback(s)",
                                  "dim"))
        if p == "custom_proxy":
            n = len(self.settings.get("custom_models") or [])
            return Text.assemble(("MODEL\n", "dim"),
                                 (f"{n} custom model(s)" if n else "none yet", "bold"))
        name = (vosk_model_info(self.settings["language"]) or ("-",))[0]
        return Text.assemble(("MODEL\n", "dim"), (name, "bold"))

    def _refresh_dashboard(self) -> None:
        try:
            self._ui("#card-provider", Button).label = self._card_provider()
            self._ui("#card-language", Button).label = self._card_language()
            self._ui("#card-model", Button).label = self._card_model()
        except Exception:
            pass
        self._refresh_nav()

    # =======================================================================
    # RECORDING INDICATOR + LEVEL METER
    # =======================================================================
    def watch_recording(self, recording: bool) -> None:
        try:
            badge = self._ui("#rec-badge", Static)
            if recording:
                badge.add_class("on")
                badge.update("* REC")
            else:
                badge.remove_class("on")
                badge.update("o idle")
                self._meter_update(0, None, 0.0)
        except Exception:
            pass

    def _blink_rec(self) -> None:
        if not self.recording:
            return
        self._rec_blink = not self._rec_blink
        try:
            self._ui("#rec-badge", Static).update(
                "* REC" if self._rec_blink else "  REC")
        except Exception:
            pass

    @staticmethod
    def _meter_render(pct: int) -> Text:
        """20-cell bar; threshold tick at cell 10 (50%)."""
        cells = int(round(pct / 5))
        filled = min(20, cells)
        bar = "█" * filled
        empty = "░" * (20 - filled)
        t = Text()
        below = filled < 10
        t.append(bar, AMBER if below else ACCENT)
        t.append(empty, "dim")
        # threshold marker line as a separate widget would misalign; use overlay char
        marked = Text.assemble(t[:10], ("|", RUST), t[10:]) if len(t) >= 10 else t
        return marked

    def _meter_update(self, pct: int, silence_remaining, elapsed: float) -> None:
        try:
            self._ui("#meter", Static).update(self._meter_render(pct))
            status = self._ui("#meter-status", Static)
            if silence_remaining is not None:
                status.update(Text.assemble(
                    (f"{elapsed:4.1f}s", "dim"),
                    (f"  silence auto-stop in {silence_remaining:.1f}s", AMBER)))
            else:
                status.update(Text.assemble((f"{elapsed:4.1f}s", "dim"),
                                            ("  live", ACCENT)))
        except Exception:
            pass

    # =======================================================================
    # HEARD PANEL + HISTORY
    # =======================================================================
    def _heard_render(self, text, stats: str) -> Text:
        if not text:
            return Text("heard:  - no check yet -", style="dim")
        return Text.assemble(("heard:\n", "dim"),
                             (text, f"bold {ACCENT}"),
                             (f"\n{stats}", "dim") if stats else ("", "dim"))

    def _set_heard(self, text: str, stats: str) -> None:
        try:
            panel = self._ui("#heard-panel", Static)
            panel.update(self._heard_render(text or "", stats))
            panel.set_class(bool(text), "filled")
        except Exception:
            pass
        if text:
            self._history.appendleft(
                (datetime.now().strftime("%H:%M:%S"),
                 self.settings["provider"], text, stats))
            self._refresh_history()

    def _refresh_history(self) -> None:
        try:
            hist = self._ui("#history", Static)
            if not self._history:
                hist.update("")
                return
            lines = [Text("recent checks:", style="dim")]
            for ts, provider, text, stats in list(self._history)[:3]:
                short = text if len(text) <= 60 else text[:57] + "..."
                lines.append(Text.assemble((f"{ts} ", "dim"), (f"{provider}: ", ""),
                                           (short, TEXT)))
            hist.update(Group(*lines))
        except Exception:
            pass

    # =======================================================================
    # DIRTY / SAVE / START
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
        if btn == "card-provider":
            self.push_screen(ProviderPickModal(self.settings),
                             self._apply_provider_pick)
        elif btn == "card-language":
            self.push_screen(LanguagePickModal(self.settings),
                             self._apply_language_pick)
        elif btn == "card-model":
            self._open_model_pick()
        elif btn == "audio-open":
            self.push_screen(AudioSettingsModal(self.settings, app_ref=self),
                             lambda _: (self._mark_dirty(),
                                        self._refresh_dashboard()))
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
        elif btn == "custom-up":
            self._custom_move(-1)
        elif btn == "custom-down":
            self._custom_move(1)
        elif btn == "custom-delete":
            self._custom_delete()
        elif btn == "whisper-download":
            self._whisper_download()
        elif btn == "mgr-delete":
            self._mgr_delete()
        elif btn == "mgr-refresh":
            self._refresh_manager()
            self._ping_proxy()
        elif btn == "test-start":
            self._start_test()
        elif btn == "test-stop":
            if self._test_stop is not None:
                self._test_stop.set()

    # ---- popup result handlers
    def _apply_provider_pick(self, key) -> None:
        if key in PROVIDERS:
            self.settings["provider"] = key
            self._mark_dirty()
            self._refresh_dashboard()
            try:
                self.notify(f"provider: {key}", title="set")
            except Exception:
                pass

    def _apply_language_pick(self, code) -> None:
        if code:
            self._select_language(code)

    def _open_model_pick(self) -> None:
        p = self.settings["provider"]
        if p == "whisper_local":
            def _apply(name):
                if name in WHISPER_MODELS:
                    self.settings["whisper_model"] = name
                    self._mark_dirty()
                    self._refresh_dashboard()
            self.push_screen(WhisperPickModal(self.settings), _apply)
        elif p == "vosk_local" and vosk_model_options(self.settings["language"]):
            def _apply(name):
                if name:
                    self._apply_model_choice(self.settings["language"], name)
            self.push_screen(VoskPickModal(self.settings), _apply)
        else:
            # gemini/custom chains need the full panes (reorder buttons)
            self._goto("gemini" if p == "gemini_proxy" else "custom")

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
                self._refresh_dashboard()
                try:
                    self.notify(f"provider: {data}", title="set")
                except Exception:
                    pass
        elif ol.id == "lang-list":
            if data.startswith("lang:"):
                self._select_language(data[len("lang:"):])
        elif ol.id == "whisper-list":
            self.settings["whisper_model"] = data
            self._mark_dirty()
            self._refresh_dashboard()
            self._reload_list("#whisper-list", self._whisper_options())
        elif ol.id == "mgr-vosk":
            self._mgr_focus = "vosk"
        elif ol.id == "mgr-whisper":
            self._mgr_focus = "whisper"

    def on_option_list_option_highlighted(self, event) -> None:
        if event.option_list.id == "provider-list":
            data = getattr(event.option, "id", None)
            try:
                self._ui("#provider-detail", Static).update(
                    self._provider_detail(data))
            except Exception:
                pass

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "lang-filter":
            lang_list = self._ui("#lang-list", OptionList)
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

    def _provider_detail(self, key) -> Text:
        if key not in PROVIDERS:
            return Text("highlight a provider to see the details",
                        style="dim")
        facts = {
            "whisper_local": lambda: f"100 languages | selected size "
                                     f"'{self.settings['whisper_model']}'"
                                     f"{' [cached]' if models_manager.whisper_model_cached(self.settings['whisper_model']) else ' [needs download]'}"
                                     f" | fully offline after download",
            "gemini_proxy": lambda: "cloud quality via your API proxy | needs "
                                    "Gemini API key(s) in the proxy | fallback "
                                    "chain of lite models",
            "custom_proxy": lambda: f"{len(self.settings.get('custom_models') or [])} "
                                    "model(s) in chain | any audio-capable model "
                                    "in provider/modelname format | proxy "
                                    "credentials required",
            "vosk_local": lambda: "~40 MB per-language models | weak-systems "
                                  "fallback | lower accuracy than whisper on "
                                  "real mic audio",
        }
        desc = PROVIDERS[key]
        head, _, tail = desc.partition(": ")
        return Text.assemble((head + "\n", f"bold {ACCENT}"),
                             (tail + "\n\n", TEXT),
                             (facts[key](), "dim"))

    # ---- language pane
    def _language_options(self, query: str):
        q = query.lower()

        def label_for(code):
            cur = "  *" if code == self.settings["language"] else ""
            return Option(f"{LANGUAGES[code]} ({code})  "
                          f"{_lang_tag(code, self.settings.get('vosk_model_overrides'))}{cur}",
                          id=f"lang:{code}")

        def header(text):
            return Option(f"-- {text} --", id=f"hdr:{text}")

        if q:
            matches = [c for c in _language_codes()
                       if q in LANGUAGES[c].lower() or q in c]
            return [label_for(c) for c in matches] or [Option("(no match)")]
        rows = [header("pinned")]
        rows += [label_for(c) for c in PINNED_LANGS]
        whisper_rest = [c for c in _language_codes()
                        if c not in PINNED_LANGS and whisper_supported(c)]
        vosk_only = [c for c in _language_codes() if not whisper_supported(c)]
        rows.append(header("whisper + more"))
        rows += [label_for(c) for c in whisper_rest]
        rows.append(header("vosk only"))
        rows += [label_for(c) for c in vosk_only]
        return rows

    def _select_language(self, code: str) -> None:
        self.settings["language"] = code
        options = vosk_model_options(code)
        if len(options) > 1:
            self.push_screen(ModelPickModal(code, options),
                             lambda name: self._apply_model_choice(code, name))
        self._mark_dirty()
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
        self._refresh_dashboard()

    # ---- whisper pane
    def _whisper_options(self):
        rows = []
        for name, desc in WHISPER_MODELS.items():
            cur = "  *" if name == self.settings["whisper_model"] else ""
            cached = models_manager.whisper_model_cached(name)
            mark = " [cached]" if cached else ""
            rows.append(Option(f"{name}  {desc}{mark}{cur}", id=name))
        return rows

    def _whisper_download(self) -> None:
        ol = self._ui("#whisper-list", OptionList)
        idx = ol.highlighted
        ids = [(getattr(o, "id", "") or "") for o in ol._options]
        if idx is None or not (0 <= idx < len(ids)) or not ids[idx]:
            return
        size = ids[idx]
        self._goto("test")
        self._test_log(f"--- preloading whisper '{size}' ---")
        self._preload_worker(size)

    @work(thread=True, group="test", exclusive=True)
    def _preload_worker(self, size: str) -> None:
        import whisper_local

        def _report(message, current, total):
            line = message + (f"  [{current}/{total} MB]" if total else "")
            self.call_from_thread(self._test_progress, message, current, total)
            self.call_from_thread(self._test_log, f"  {line}")

        try:
            whisper_local.configure(model_size=size, progress=_report)
            whisper_local.get_model(self.settings["language"])
        except Exception as e:
            self.call_from_thread(self._test_log, f"[ERROR] {e}")
        finally:
            self.call_from_thread(self._refresh_dashboard)

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
        ol = self._ui("#gemini-list", OptionList)
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
            entry = self._ui("#custom-input", Input).value.strip()
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
            self._ui("#custom-input", Input).value = ""
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
        ol = self._ui("#custom-list", OptionList)
        idx = ol.highlighted
        if idx is None or not (0 <= idx < len(self._custom_order)):
            return None
        return idx

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
    def _mgr_active_names(self):
        """Model names currently in active use (for the star marker)."""
        names = set()
        if self.settings["provider"] == "whisper_local":
            names.add(f"faster-whisper-{self.settings['whisper_model']}")
        info = vosk_model_info(self.settings["language"])
        if self.settings["provider"] == "vosk_local" and info:
            names.add(info[0])
        return names

    def _mgr_vosk_options(self):
        entries = models_manager.list_vosk_models()
        if not entries:
            return [Option("(nothing downloaded)", id="empty")]
        active = self._mgr_active_names()
        return [Option(f"{name}  ~{size} MB" +
                       ("  * active" if name in active else ""), id=str(path))
                for name, path, size in entries]

    def _mgr_whisper_options(self):
        entries = models_manager.list_whisper_models()
        if not entries:
            return [Option("(nothing downloaded)", id="empty")]
        active = self._mgr_active_names()
        return [Option(f"{name}  ~{size} MB" +
                       ("  * active" if name in active else ""), id=str(path))
                for name, path, size in entries]

    def _refresh_manager(self) -> None:
        try:
            vosk_list = self._ui("#mgr-vosk", OptionList)
            vosk_list.clear_options()
            vosk_list.add_options(self._mgr_vosk_options())
            whisper_list = self._ui("#mgr-whisper", OptionList)
            whisper_list.clear_options()
            whisper_list.add_options(self._mgr_whisper_options())
            total = (sum(e[2] for e in models_manager.list_vosk_models()) +
                     sum(e[2] for e in models_manager.list_whisper_models()))
            self._ui("#mgr-location", Static).update(
                Text(f"vosk: {models_manager.VOSK_DIR}\n"
                     f"whisper: {models_manager.HF_HUB_DIR}\n"
                     f"total on disk: ~{total} MB  |  * = in active use",
                     style=MUTED))
        except Exception:
            pass
        self._refresh_dashboard()

    def _mgr_delete(self) -> None:
        ol_id = "#mgr-vosk" if self._mgr_focus == "vosk" else "#mgr-whisper"
        ol = self._ui(ol_id, OptionList)
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
        ol = self._ui(selector, OptionList)
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
            bar = self._ui("#test-progress", ProgressBar)
            status = self._ui("#test-status", Static)
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
            log = self._ui("#test-log", RichLog)
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
            self._ui("#test-start", Button).disabled = running
            self._ui("#test-stop", Button).disabled = not running
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
        if "on_level" in params:
            def _on_level(pct, silence_remaining, elapsed):
                self.call_from_thread(self._meter_update, pct,
                                      silence_remaining, elapsed)
            kwargs["on_level"] = _on_level

        def _report(message, current, total):
            line = message + (f"  [{current}/{total} MB]" if total else "")
            self.call_from_thread(self._test_progress, message, current, total)
            self.call_from_thread(self._test_log, f"  {line}")

        heard = ""
        stats = ""
        try:
            import providers
            if not providers.prepare_model(settings, report=_report):
                self.call_from_thread(self._test_log,
                                      "[WARN] model/proxy not ready")
            import time as _time
            t1 = _time.perf_counter()
            heard = test_func(settings, **kwargs) or ""
            stats = f"transcribed in {_time.perf_counter() - t1:.1f}s"
        except TypeError:
            heard = test_func(settings) or ""
        except Exception as e:
            self.call_from_thread(self._test_log, f"[ERROR] {e}")
        finally:
            self.call_from_thread(self._set_heard, heard, stats)
            self.call_from_thread(self._set_test_running, False)
            self.call_from_thread(setattr, self, "recording", False)
            self.call_from_thread(self._refresh_dashboard)

    # =======================================================================
    # DIAGNOSTICS LOG PANE
    # =======================================================================
    def action_toggle_log(self) -> None:
        try:
            pane = self._ui("#logpane")
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
            log = self._ui("#applog", RichLog)
            for levelno, line in records:
                style = BAD if levelno >= logging.ERROR else (
                    AMBER if levelno >= logging.WARNING else MUTED)
                log.write(Text(line, style=style))
            if auto_open:
                self._ui("#logpane").display = True
        except Exception:
            pass


HOME_INTRO_TEXT = ("Configure your rig, then go live.\n"
                   "Everything is one click away - and the mouse works everywhere.")


def run_tui(settings, on_test=None, wizard=None, **_kwargs):
    """Run the PDA console. Returns settings on GO LIVE.

    wizard: force the first-run wizard on/off (default: auto-detect from the
    absence of a settings file). Raises SystemExit(0) on quit-without-start.
    """
    if wizard is None:
        from settings import SETTINGS_FILE
        wizard = not SETTINGS_FILE.exists()

    # hand the splash baton to the loading screen, then close the splash
    # right before Textual paints (the loader takes over from here)
    try:
        import pyi_splash  # type: ignore
        pyi_splash.update_text("warming up the PDA...")
    except Exception:
        pass

    app = MicApp(settings, test_func=on_test, wizard=wizard)

    def _close_splash_once():
        try:
            import pyi_splash  # type: ignore
            pyi_splash.close()
        except Exception:
            pass

    # close as soon as the app has painted its first frame
    original_on_mount = MicApp.on_mount

    def mounted(self):
        original_on_mount(self)
        _close_splash_once()

    MicApp.on_mount = mounted
    try:
        result = app.run()
    finally:
        MicApp.on_mount = original_on_mount
    if result is None:
        print("Exiting without starting the microphone service.")
        raise SystemExit(0)
    return result
