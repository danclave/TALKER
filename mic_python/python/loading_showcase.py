# loading_showcase.py - interactive gallery of loading-screen concepts
# for the TALKER PDA. Dev tool: page through 10 animated variants and
# pick favorites. Not shipped in the exe.
#
#   run:  .venv\Scripts\python.exe -X utf8 loading_showcase.py
#   keys: <- / ->  or N / P   next / previous variant
#         1-9, 0               jump to variant
#         space                pause/resume the animation
#         q                    quit

import math
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.text import Text
from rich import box

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Static

# ---------------------------------------------------------------- art & palette
ART = [
    "████████╗ █████╗ ██╗     ██╗  ██╗███████╗██████╗ ",
    "╚══██╔══╝██╔══██╗██║     ██║ ██╔╝██╔════╝██╔══██╗",
    "   ██║   ███████║██║     █████╔╝ █████╗  ██████╔╝",
    "   ██║   ██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗",
    "   ██║   ██║  ██║███████╗██║  ██╗███████╗██║  ██║",
    "   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝",
]
ROWS = len(ART)
WIDTH = max(len(r) for r in ART)
CELLS = sum(len(r) for r in ART)

BG = "#060a06"
ACCENT = "#8aff5a"
DIM_GREEN = "#1d3316"
TEXT = "#cfe6c3"
MUTED = "#5f735f"
AMBER = "#ffb000"
RUST = "#c97b3d"
WHITE = "#e8ffe0"

GLYPHS = "▓▒░#$%&@?!/\\|"


def _h(n: int, salt: int = 0) -> float:
    """Deterministic pseudo-random in [0,1) - keeps animations reproducible."""
    return ((n * 2654435761 + salt * 40503 + 0x9E3779B1) % 100000) / 100000.0


def _cell_index(r: int, c: int) -> int:
    return r * WIDTH + c


def _char(r: int, c: int) -> str:
    return ART[r][c] if c < len(ART[r]) else " "


def _is_blank(r: int, c: int) -> bool:
    return _char(r, c) == " "


def _segmented_bar(progress: float, width: int = 30) -> Text:
    """Chunky segmented PDA bar with tick marks."""
    filled = int(progress * width)
    bar = Text()
    for i in range(width):
        if i < filled:
            bar.append("▮", ACCENT)
        elif i == filled and progress > 0:
            bar.append("▮", AMBER)
        else:
            bar.append("▯", DIM_GREEN)
    bar.append(f"  {int(progress * 100):3d}%", MUTED)
    return bar


def _classic_fill(progress: float) -> Text:
    t = Text()
    remaining = int(progress * CELLS)
    for r in range(ROWS):
        filled = max(0, min(len(ART[r]), remaining))
        t.append(ART[r][:filled], ACCENT)
        t.append(ART[r][filled:], DIM_GREEN)
        t.append("\n")
        remaining -= filled
    return t


# ---------------------------------------------------------------- variants
class Variant:
    name = "variant"

    def render(self, progress: float, frame: int) -> RenderableType:
        raise NotImplementedError


class V1ClassicFill(Variant):
    name = "1. Classic Fill + segmented bar"

    def render(self, progress, frame):
        return Group(
            _classic_fill(progress),
            Text(" "),
            _segmented_bar(progress),
        )


class V2ScanlineSweep(Variant):
    name = "2. Scanline Sweep (beam travels down)"

    def render(self, progress, frame):
        beam_row = progress * (ROWS + 1)
        t = Text()
        for r in range(ROWS):
            if r < beam_row - 0.2:
                style = ACCENT
            elif r <= beam_row:
                style = WHITE          # the bright beam itself
            else:
                style = DIM_GREEN
            t.append(ART[r], style)
            t.append("\n")
        pos = int(progress * WIDTH)
        t.append(" " * pos, "")
        t.append("▼", AMBER)
        t.append("\n")
        t.append(Text.assemble(("sweep ", MUTED),
                               ("▮" * pos, AMBER),
                               ("▯" * (WIDTH - pos), DIM_GREEN)))
        return Group(t)


class V3RadialBloom(Variant):
    name = "3. Radial Bloom (grows from center)"

    def render(self, progress, frame):
        cr, cc = (ROWS - 1) / 2, (WIDTH - 1) / 2
        max_r = math.hypot(cr, cc)
        radius = progress * max_r
        t = Text()
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                d = math.hypot(r - cr, c - cc)
                if d < radius - 1.2:
                    t.append(ch, ACCENT)
                elif d <= radius:
                    t.append(ch, AMBER)     # glowing edge ring
                else:
                    t.append(ch, DIM_GREEN)
            t.append("\n")
        t.append(Text.assemble(("bloom radius ", MUTED),
                               (f"{radius / max_r * 100:3.0f}% ", TEXT),
                               ("◎", AMBER)))
        return Group(t)


class V4GeigerTicks(Variant):
    name = "4. Geiger Ticks (random clicks + geiger meter)"

    def render(self, progress, frame):
        t = Text()
        lit = 0
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                i = _cell_index(r, c)
                if _h(i) <= progress:
                    # freshly-clicked cells flash amber for a moment
                    age = progress - _h(i)
                    t.append(ch, AMBER if age < 0.03 else ACCENT)
                    lit += 1
                else:
                    t.append(ch, DIM_GREEN)
            t.append("\n")
        # geiger meter: segments fire in noisy order, not left-to-right
        seg = 24
        bar = Text()
        fired = sum(1 for i in range(seg) if _h(i, salt=7) <= progress)
        for i in range(seg):
            if _h(i, salt=7) <= progress:
                bar.append("⣿", ACCENT)
            elif _h(i, salt=7) - progress < 0.06 and (frame // 2) % 2 == 0:
                bar.append("⣷", AMBER)      # about to fire, flickering
            else:
                bar.append("⣀", DIM_GREEN)
        clicks = int(lit * 137 / max(1, CELLS) * 100)
        return Group(
            t,
            Text(" "),
            Text.assemble(("CLICKS ", MUTED), (f"{clicks:4d}", AMBER), ("  ", ""),
                          bar),
        )


class V5GlitchBoot(Variant):
    name = "5. Glitch Boot (corruption resolves into text)"

    def render(self, progress, frame):
        t = Text()
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                i = _cell_index(r, c)
                if _h(i, salt=3) <= progress:
                    t.append(ch, ACCENT)
                elif _h(i, salt=frame // 3) < 0.4:
                    g = GLYPHS[int(_h(i, salt=frame) * len(GLYPHS))]
                    t.append(g, AMBER if _h(i, salt=frame // 2) < 0.5 else MUTED)
                else:
                    t.append(ch, DIM_GREEN)
            t.append("\n")
        # noisy block bar with glitch glyphs in the head
        w = 30
        filled = int(progress * w)
        bar = Text()
        for i in range(w):
            if i < filled - 2:
                bar.append("█", ACCENT)
            elif i < filled:
                g = GLYPHS[int(_h(i, salt=frame) * len(GLYPHS))]
                bar.append(g, AMBER)
            else:
                bar.append("░", DIM_GREEN)
        return Group(t, Text(" "), bar)


class V6MatrixRain(Variant):
    name = "6. Matrix Rain (drops paint the letters)"

    def render(self, progress, frame):
        t = Text()
        for c in range(WIDTH):
            speed = 0.35 + _h(c, salt=11) * 0.9
            drop = (frame * speed + _h(c, salt=5) * 14) % (ROWS + 6)
            for r in range(ROWS):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                if c / WIDTH <= progress and drop > r:
                    head = drop - r
                    t.append(ch, WHITE if head < 0.8 else ACCENT)
                elif 0 < drop - r <= 3 and c / WIDTH > progress:
                    g = "0123456789абвгд"[int(_h(r * WIDTH + c, salt=frame) * 15)]
                    t.append(g, MUTED)
                else:
                    t.append(ch, DIM_GREEN)
            if c < WIDTH - 1:
                pass
        # rebuild line by line (the loop above appended horizontally then
        # newline per row would be wrong) -> simpler: re-render per row below
        rows = []
        for r in range(ROWS):
            line = Text()
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    line.append(" ")
                    continue
                speed = 0.35 + _h(c, salt=11) * 0.9
                drop = (frame * speed + _h(c, salt=5) * 14) % (ROWS + 6)
                if c / WIDTH <= progress and drop > r:
                    head = drop - r
                    line.append(ch, WHITE if head < 0.8 else ACCENT)
                elif 0 < drop - r <= 3:
                    g = "0123456789абвгд"[int(_h(r * WIDTH + c, salt=frame) * 15)]
                    line.append(g, MUTED)
                else:
                    line.append(ch, DIM_GREEN)
            rows.append(line)
        # drop the horizontal append above; assemble rows
        out = Text()
        for i, line in enumerate(rows):
            out.append(line)
            out.append("\n")
        out.append(Text.assemble(("rain coverage ", MUTED),
                                 (f"{int(progress * 100):3d}%", TEXT)))
        return Group(out)


class V7RadarSweep(Variant):
    name = "7. Radar Sweep (rotating beam ignites cells)"

    def render(self, progress, frame):
        cr, cc = (ROWS - 1) / 2, 0        # emitter at left edge, middle
        swept = progress * 2 * math.pi * 1.0   # one full rotation
        t = Text()
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                ang = math.atan2(-(r - cr), c - cc)  # 0 = east, ccw
                if ang < 0:
                    ang += 2 * math.pi
                if ang < swept:
                    recency = swept - ang
                    if recency < 0.5:
                        t.append(ch, WHITE)
                    elif recency < 1.6:
                        t.append(ch, AMBER)
                    else:
                        t.append(ch, ACCENT)
                else:
                    t.append(ch, DIM_GREEN)
            t.append("\n")
        # angular gauge
        seg = 24
        arc = Text()
        for i in range(seg):
            a = i / seg * 2 * math.pi
            arc.append("●" if a < swept else "○", ACCENT if a < swept else DIM_GREEN)
        arc.append("  TARGET LOCK" if progress >= 0.999 else "  sweeping…", AMBER)
        return Group(t, Text(" "), arc)


class V8SinePulse(Variant):
    name = "8. Sine Pulse (wave rides through, then locks)"

    def render(self, progress, frame):
        phase = progress * (WIDTH * 0.55 + math.pi)
        t = Text()
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                x = phase - c * 0.55
                if x > math.pi:
                    t.append(ch, ACCENT)          # wave passed: locked green
                elif x < -0.2:
                    t.append(ch, DIM_GREEN)
                else:
                    s = math.sin(x)
                    if s > 0.75:
                        t.append(ch, WHITE)       # crest
                    elif s > 0:
                        t.append(ch, AMBER)
                    else:
                        t.append(ch, DIM_GREEN)
            t.append("\n")
        # wave bar: little vertical bars of sin height
        bar = Text()
        for i in range(30):
            s = math.sin(phase - i * 0.55)
            bar.append("▁▂▃▄▅▆▇"[max(0, min(6, int((s + 1) * 3)))], AMBER if s > 0 else MUTED)
        bar.append(f"  {int(progress * 100):3d}%", MUTED)
        return Group(t, Text(" "), bar)


class V9CRTPowerOn(Variant):
    name = "9. CRT Power-On (line unfolds into the screen)"

    def render(self, progress, frame):
        p = progress
        t = Text()
        if p < 0.22:
            # bright horizontal line grows from center
            w = int((p / 0.22) * WIDTH)
            pad = (WIDTH - w) // 2
            t.append(" " * pad)
            t.append("▔" * w, WHITE)
        elif p < 0.55:
            # line expands vertically into the full art, still white-hot
            rows_shown = 1 + int(((p - 0.22) / 0.33) * (ROWS - 1))
            for r in range(ROWS):
                if r < rows_shown:
                    t.append(ART[r], WHITE)
                t.append("\n" if r < rows_shown - 1 else "")
        else:
            # settle: white -> LCD green
            mix = (p - 0.55) / 0.45
            t.append(_classic_fill(1.0 if mix >= 0.5 else 0.999))
            # recolor by simple re-render with blended style choice
            t = Text()
            for r in range(ROWS):
                t.append(ART[r], ACCENT if mix > 0.4 else WHITE)
                t.append("\n")
        t.append("\n")
        t.append(Text.assemble(("filament ", MUTED),
                               ("▮▮▮▮▮▮▮▮▮▮"[max(0, int(p * 10) - (0 if p < 1 else 1)):][:10] or "░", AMBER),
                               (f"  {int(p * 100):3d}%", MUTED)))
        return Group(t)


class V10BootLog(Variant):
    name = "10. Boot Log (art fills while firmware boots)"

    LOG = [
        "PDA firmware 2.2.6-anomaly",
        "cpu: R5000 @ 333MHz ......... [OK]",
        "mem check 64MB .............. [OK]",
        "radiation sensor ............ [OK]",
        "anomaly mapper .............. [OK]",
        "audio core (16kHz) .......... [OK]",
        "geiger counter .............. [OK]",
        "encrypting channel .......... [OK]",
        "linking zone network ........ [OK]",
        "loading personality DB ...... [OK]",
    ]

    def render(self, progress, frame):
        art = _classic_fill(min(1.0, progress * 1.15))
        shown = int(progress * len(self.LOG))
        log = Text()
        for i, line in enumerate(self.LOG):
            if i < shown:
                ok = "[OK]" in line
                log.append(f"  {line}\n", ACCENT if ok else MUTED)
            elif i == shown:
                # typing effect on the current line
                chars = int((_h(i, salt=frame) * 0.4 + 0.6) * len(line))
                log.append(f"  {line[:chars]}", TEXT)
                log.append("▌", AMBER)
                log.append("\n")
        if progress >= 0.999:
            log.append("\n  ", ACCENT)
            log.append("■ READY ■", f"bold {AMBER}")
        # side-by-side: art left, log right
        art_lines = art.plain.split("\n")
        log_lines = log.plain.split("\n")
        combined = Text()
        for r in range(max(len(art_lines), len(log_lines))):
            a = art_lines[r] if r < len(art_lines) else ""
            l = log_lines[r] if r < len(log_lines) else ""
            combined.append(a.ljust(WIDTH + 2), ACCENT if a.strip() else "")
            combined.append(l, MUTED)
            combined.append("\n")
        combined.append(_segmented_bar(progress))
        return Group(combined)


VARIANTS = [V1ClassicFill(), V2ScanlineSweep(), V3RadialBloom(), V4GeigerTicks(),
            V5GlitchBoot(), V6MatrixRain(), V7RadarSweep(), V8SinePulse(),
            V9CRTPowerOn(), V10BootLog()]


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
        for p in (0.0, 0.33, 0.66, 1.0):
            for frame in (0, 7):
                out = variant.render(p, frame)
                console.print(out)
    text = console.file.getvalue()
    assert len(text) > 1000, "render output suspiciously small"
    print(f"SELFTEST RENDER OK: {len(VARIANTS)} variants x 4 steps x 2 frames")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest_render()
    else:
        ShowcaseApp().run()
