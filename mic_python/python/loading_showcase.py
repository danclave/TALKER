# loading_showcase.py - interactive gallery of loading-screen concepts
# for the TALKER PDA. Dev tool: page through animated variants and
# pick favorites. Not shipped in the exe. The variant render library
# lives in loading_variants.py (shared with the real boot screen).
#
#   run:  .venv\Scripts\python.exe -X utf8 loading_showcase.py
#   keys: <- / ->  or N / P   next / previous variant
#         1-9, 0               jump to variant 1-10
#         space                pause/resume the animation
#         q                    quit
#
# The 10 BOOT_VARIANTS (the curated boot set) are shown FIRST, the
# remaining gallery pieces after them.

import math

from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.text import Text
from rich import box

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Static

from loading_variants import BOOT_VARIANTS, ALL_VARIANTS

_boot_names = {v.name for v in BOOT_VARIANTS}
VARIANTS = list(BOOT_VARIANTS) + [v for v in ALL_VARIANTS
                                  if v.name not in _boot_names]


# ---------------------------------------------------------------- showcase app
class ShowcaseApp(App):
    CSS = """
    Screen { background: #060a06; align: center middle; }
    #stage { width: auto; }
    """
    BINDINGS = [
        Binding("right,n", "next", "Next"),
        Binding("left,p", "prev", "Prev"),
        Binding("space", "pause", "Pause"),
        Binding("q", "quit", "Quit"),
        Binding("1", "jump(0)", show=False), Binding("2", "jump(1)", show=False),
        Binding("3", "jump(2)", show=False), Binding("4", "jump(3)", show=False),
        Binding("5", "jump(4)", show=False), Binding("6", "jump(5)", show=False),
        Binding("7", "jump(6)", show=False), Binding("8", "jump(7)", show=False),
        Binding("9", "jump(8)", show=False), Binding("0", "jump(9)", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.index = 0
        self.progress = 0.0
        self.frame = 0
        self.paused = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="stage")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "TALKER loading-screen showcase"
        self.set_interval(1 / 15, self._tick)
        self._render_stage()

    def _tick(self) -> None:
        self.frame += 1
        if not self.paused:
            self.progress += 0.01
            if self.progress > 1.005:
                self.progress = 0.0
        self._render_stage()

    def _render_stage(self) -> None:
        variant = VARIANTS[self.index]
        body = variant.render(min(1.0, self.progress), self.frame)
        panel = Panel(
            body,
            title=f"[{ACCENT}]{variant.name}[/]   "
                  f"[dim]{self.index + 1}/{len(VARIANTS)}[/]",
            title_align="left",
            border_style=RUST,
            box=box.ROUNDED,
            padding=(0, 2),
        )
        try:
            self.query_one("#stage", Static).update(panel)
        except Exception:
            pass

    def action_next(self) -> None:
        self.index = (self.index + 1) % len(VARIANTS)
        self.progress = 0.0
        self._render_stage()

    def action_prev(self) -> None:
        self.index = (self.index - 1) % len(VARIANTS)
        self.progress = 0.0
        self._render_stage()

    def action_jump(self, i: int) -> None:
        self.index = i
        self.progress = 0.0
        self._render_stage()

    def action_pause(self) -> None:
        self.paused = not self.paused


def _selftest_render():
    """Every variant must render at several progress points without raising,
    producing non-empty output."""
    import io
    console = Console(file=io.StringIO(), force_terminal=False, width=110)
    for variant in VARIANTS:
        for p in (0.0, 0.12, 0.33, 0.5, 0.66, 0.9, 1.0):
            for frame in (0, 7):
                out = variant.render(p, frame)
                console.print(out)
    text = console.file.getvalue()
    assert len(text) > 2000, "render output suspiciously small"
    # bars must be gone from Radial Bloom & Matrix Rain (user directive)
    for idx, vname in ((1, "Radial Bloom"), (3, "Matrix Rain")):
        buf = io.StringIO()
        c2 = Console(file=buf, force_terminal=False, width=110)
        for p in (0.2, 0.5, 0.8):
            c2.print(VARIANTS[idx].render(p, 0))
        out = buf.getvalue()
        assert "▮" not in out and "%" not in out, \
            f"{vname} must not carry a progress readout"
    print(f"SELFTEST RENDER OK: {len(VARIANTS)} variants x 7 steps x 2 frames"
          " (+ bloom/rain bar-free)")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest_render()
    else:
        ShowcaseApp().run()


def _selftest_render():
    """Every variant must render at several progress points without raising,
    producing non-empty output."""
    import io
    console = Console(file=io.StringIO(), force_terminal=False, width=110)
    for variant in VARIANTS:
        for p in (0.0, 0.12, 0.33, 0.5, 0.66, 0.9, 1.0):
            for frame in (0, 7):
                console.print(variant.render(p, frame))
    text = console.file.getvalue()
    assert len(text) > 2000, "render output suspiciously small"
    # bars must be gone from Radial Bloom & Matrix Rain (user directive)
    names = [v.name for v in VARIANTS]
    for vname in ("Radial Bloom", "Matrix Rain"):
        idx = names.index(vname)
        buf = io.StringIO()
        c2 = Console(file=buf, force_terminal=False, width=110)
        for p in (0.2, 0.5, 0.8):
            c2.print(VARIANTS[idx].render(p, 0))
        out = buf.getvalue()
        assert "▮" not in out and "%" not in out, \
            f"{vname} must not carry a progress readout"
    assert len(BOOT_VARIANTS) == 10, "curated boot set must be 10"
    print(f"SELFTEST RENDER OK: {len(VARIANTS)} variants x 7 steps x 2 frames"
          " (+ bloom/rain bar-free, boot set = 10)")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest_render()
    else:
        ShowcaseApp().run()
