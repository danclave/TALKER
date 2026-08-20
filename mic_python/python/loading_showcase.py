# loading_showcase.py - interactive gallery of loading-screen concepts
# for the TALKER PDA. Dev tool: page through animated variants and
# pick favorites. Not shipped in the exe.
#
#   run:  .venv\Scripts\python.exe -X utf8 loading_showcase.py
#   keys: <- / ->  or N / P   next / previous variant
#         1-9, 0               jump to variant 1-10
#         space                pause/resume the animation
#         q                    quit
#
# FUTURE INTEGRATION NOTES (user directives):
#   - do NOT sync the animation to actual init progress - it kills the fun;
#     play it at its own (slightly sped-up) pace
#   - any key skips: stop the animation, wait for real init, go straight
#     to the TUI

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
SOFT_GREEN = "#5fae3c"

GLYPHS = "▓▒░#$%&@?!/\\|"
CIPHERS = "ΔΘΛΞΠΣΦΨΩᚠᚢᚦᚨᚱᚲ"
DUST = "·¸°˙"


def _h(n: int, salt: int = 0) -> float:
    """Deterministic pseudo-random in [0,1) - keeps animations reproducible."""
    return ((n * 2654435761 + salt * 40503 + 0x9E3779B1) % 100000) / 100000.0


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


def _hash_order_cells():
    """All non-blank (r, c) cells sorted by their hash - 'random' fill order."""
    cells = [(r, c) for r in range(ROWS) for c in range(WIDTH)
             if not _is_blank(r, c)]
    cells.sort(key=lambda rc: _h(rc[0] * WIDTH + rc[1]))
    return cells


# ---------------------------------------------------------------- variants
class Variant:
    name = "variant"

    def render(self, progress: float, frame: int) -> RenderableType:
        raise NotImplementedError


# ============ the keepers (user picks, round 1) ============

class VClassicFill(Variant):
    name = "Classic Fill + segmented bar"

    def render(self, progress, frame):
        return Group(_classic_fill(progress), Text(" "), _segmented_bar(progress))


class VRadialBloom(Variant):
    name = "Radial Bloom"          # bar removed per user

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
        return Group(t)


class VGeigerTicks(Variant):
    name = "Geiger Ticks"

    def render(self, progress, frame):
        t = Text()
        lit = 0
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                i = r * WIDTH + c
                if _h(i) <= progress:
                    age = progress - _h(i)
                    t.append(ch, AMBER if age < 0.03 else ACCENT)
                    lit += 1
                else:
                    t.append(ch, DIM_GREEN)
            t.append("\n")
        seg = 24
        bar = Text()
        for i in range(seg):
            if _h(i, salt=7) <= progress:
                bar.append("⣿", ACCENT)
            elif _h(i, salt=7) - progress < 0.06 and (frame // 2) % 2 == 0:
                bar.append("⣷", AMBER)
            else:
                bar.append("⣀", DIM_GREEN)
        clicks = int(lit * 137 / max(1, CELLS) * 100)
        return Group(t, Text(" "),
                     Text.assemble(("CLICKS ", MUTED), (f"{clicks:4d}", AMBER),
                                   ("  ", ""), bar))


class VMatrixRain(Variant):
    name = "Matrix Rain"           # bar removed per user

    def render(self, progress, frame):
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
        out = Text()
        for line in rows:
            out.append(line)
            out.append("\n")
        return Group(out)


class VSinePulse(Variant):
    name = "Sine Pulse"

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
                    t.append(ch, ACCENT)
                elif x < -0.2:
                    t.append(ch, DIM_GREEN)
                else:
                    s = math.sin(x)
                    if s > 0.75:
                        t.append(ch, WHITE)
                    elif s > 0:
                        t.append(ch, AMBER)
                    else:
                        t.append(ch, DIM_GREEN)
            t.append("\n")
        bar = Text()
        for i in range(30):
            s = math.sin(phase - i * 0.55)
            bar.append("▁▂▃▄▅▆▇"[max(0, min(6, int((s + 1) * 3)))],
                       AMBER if s > 0 else MUTED)
        bar.append(f"  {int(progress * 100):3d}%", MUTED)
        return Group(t, Text(" "), bar)


class VCRTPowerOn(Variant):
    name = "CRT Power-On"

    def render(self, progress, frame):
        p = progress
        t = Text()
        if p < 0.22:
            w = int((p / 0.22) * WIDTH)
            pad = (WIDTH - w) // 2
            t.append(" " * pad)
            t.append("▔" * w, WHITE)
        elif p < 0.55:
            rows_shown = 1 + int(((p - 0.22) / 0.33) * (ROWS - 1))
            for r in range(ROWS):
                if r < rows_shown:
                    t.append(ART[r], WHITE)
                t.append("\n" if r < rows_shown - 1 else "")
        else:
            mix = (p - 0.55) / 0.45
            for r in range(ROWS):
                t.append(ART[r], ACCENT if mix > 0.4 else WHITE)
                t.append("\n")
        t.append("\n")
        t.append(Text.assemble(
            ("filament ", MUTED),
            ("▮" * max(0, 10 - int(p * 10)) + "░" * int(p * 10), AMBER)))
        return Group(t)


class VBootLog(Variant):
    name = "Boot Log"

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
                log.append(f"  {line}\n", ACCENT if "[OK]" in line else MUTED)
            elif i == shown:
                chars = int((_h(i, salt=frame) * 0.4 + 0.6) * len(line))
                log.append(f"  {line[:chars]}", TEXT)
                log.append("▌", AMBER)
                log.append("\n")
        if progress >= 0.999:
            log.append("\n  ", ACCENT)
            log.append("■ READY ■", f"bold {AMBER}")
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


# ============ new batch (round 2) ============

class VPowerFault(Variant):
    name = "Power Fault"

    """Faulty battery: the screen flickers; cells only lock during 'power
    good' windows - with a blinking charge icon."""

    def render(self, progress, frame):
        # power is 'good' in irregular windows; flicker via frame parity
        good = _h(frame // 3, salt=21) > 0.35
        surge = not good and _h(frame, salt=22) < 0.5
        t = Text()
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                i = r * WIDTH + c
                if _h(i, salt=2) <= progress:
                    if good:
                        t.append(ch, ACCENT)
                    elif surge and _h(i, salt=frame) < 0.3:
                        t.append(ch, WHITE)      # power surge flash
                    else:
                        t.append(ch, DIM_GREEN)  # browned out
                else:
                    t.append(ch, DIM_GREEN)
            t.append("\n")
        icon = "⚡" if good or surge else "·"
        cells_lit = sum(1 for i in range(ROWS * WIDTH)
                        if _h(i, salt=2) <= progress)
        t.append(Text.assemble(
            ((icon + " ") if (frame // 2) % 2 == 0 else "  "), AMBER,
            ("CHARGE ", MUTED),
            (f"{cells_lit * 100 // max(1, sum(1 for r in range(ROWS) for c in range(WIDTH) if not _is_blank(r,c)))}%", TEXT),
            ("  " + ("POWER GOOD" if good else "BROWN-OUT"), ACCENT if good else BAD_COLOR),
        ))
        return Group(t)


BAD_COLOR = "#ff5544"


class VDustWind(Variant):
    name = "Dust Wind"

    """Zone wind blows dust off the letters; each row clears at its own
    speed, drifting particles trailing the front."""

    def render(self, progress, frame):
        t = Text()
        for r in range(ROWS):
            lag = _h(r, salt=31) * 6          # per-row wind delay
            front = progress * (WIDTH + 8) - lag
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    # stray particles drifting over blanks
                    if front > c and _h(r * WIDTH + c, salt=frame // 4) < 0.06:
                        t.append(DUST[int(_h(r + c, salt=frame) * 4) % 4], MUTED)
                    else:
                        t.append(" ")
                    continue
                d = front - c
                if d > 2:
                    t.append(ch, ACCENT)          # dust blown off
                elif d > 0:
                    t.append(ch, AMBER)           # clearing edge
                else:
                    # still buried: show dust glyph sometimes
                    if _h(r * WIDTH + c, salt=frame // 2) < 0.25:
                        t.append(DUST[int(_h(c, salt=frame) * 4) % 4], MUTED)
                    else:
                        t.append(ch, DIM_GREEN)
            t.append("\n")
        t.append(Text.assemble(("wind ", MUTED),
                               ("≈".rjust(6, "≈"), TEXT if (frame // 3) % 2 else MUTED)))
        return Group(t)


class VOscilloscope(Variant):
    name = "Oscilloscope Trace"

    """A scope beam sweeps left to right lighting the trace; the live beam
    column glows white. A waveform strip runs underneath."""

    def render(self, progress, frame):
        trace_x = progress * WIDTH
        t = Text()
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                d = trace_x - c
                if d > 1.5:
                    t.append(ch, ACCENT)
                elif d > 0:
                    t.append(ch, WHITE)       # the beam itself
                else:
                    t.append(ch, DIM_GREEN)
            t.append("\n")
        # live waveform strip (decorative, not a progress bar)
        wave = Text()
        for i in range(WIDTH):
            s = math.sin(i * 0.35 + frame * 0.25) * 0.7 + \
                (_h(i, salt=frame // 2) - 0.5) * 0.3
            if i < trace_x:
                wave.append("▁▂▃▄▅▆▇"[max(0, min(6, int((s + 1) * 3)))], ACCENT)
            else:
                wave.append("─", DIM_GREEN)
        wave.append("  ▲", AMBER if (frame // 2) % 2 else MUTED)
        return Group(t, Text(" "), wave)


class VCipherDecrypt(Variant):
    name = "Cipher Decrypt"

    """The art arrives encrypted in runes; a decode wave sweeps left to
    right replacing ciphertext with plaintext."""

    def render(self, progress, frame):
        front = progress * WIDTH
        t = Text()
        encoded = 0
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                i = r * WIDTH + c
                d = front - c
                if d > 2:
                    t.append(ch, ACCENT)                       # decoded
                elif d > 0:
                    t.append(ch, AMBER)                        # decoding
                else:
                    g = CIPHERS[int(_h(i, salt=frame // 3) * len(CIPHERS))]
                    t.append(g, MUTED)
                    encoded += 1
            t.append("\n")
        t.append(Text.assemble(("DECRYPTING ", MUTED),
                               (f"{encoded:3d}", AMBER),
                               (" cipher cells", MUTED)))
        return Group(t)


class VZoneDawn(Variant):
    name = "Zone Dawn"

    """Sunrise over the art: a glowing horizon rises row by row; below it
    the world is lit, above still dark. A small sun climbs the edge."""

    def render(self, progress, frame):
        horizon = ROWS - 1 - progress * (ROWS + 1)
        t = Text()
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                if r > horizon + 0.8:
                    t.append(ch, ACCENT)
                elif r > horizon - 0.2:
                    t.append(ch, AMBER)        # the dawn line
                else:
                    t.append(ch, DIM_GREEN)
            if horizon >= r - 0.5 and horizon <= r + 0.5:
                t.append("  ☀", AMBER)         # sun riding the horizon
            t.append("\n")
        return Group(t)


class VThermalSweep(Variant):
    name = "Thermal Sweep"

    """A heat wave passes through: cells go white-hot, cool through amber
    and settle green - with a falling core-temp readout."""

    def render(self, progress, frame):
        front = progress * WIDTH
        t = Text()
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                d = front - c
                if d <= 0:
                    t.append(ch, DIM_GREEN)
                elif d < 2:
                    t.append(ch, WHITE)
                elif d < 5:
                    t.append(ch, AMBER)
                elif d < 9:
                    t.append(ch, SOFT_GREEN)
                else:
                    t.append(ch, ACCENT)
            t.append("\n")
        temp = int(900 - progress * 780)
        t.append(Text.assemble(("CORE TEMP ", MUTED), (f"{temp:4d}°C",
                               AMBER if temp > 300 else ACCENT)))
        return Group(t)


class VCircuitCurrent(Variant):
    name = "Circuit Current"

    """Current traces a path through the letters: the head glows white with
    an amber trail, junctions stay lit behind it."""

    def render(self, progress, frame):
        cells = _hash_order_cells()
        visited = int(progress * len(cells))
        head = visited - 1
        lit_ranks = {}
        for rank, (r, c) in enumerate(cells[:visited]):
            lit_ranks[(r, c)] = rank
        t = Text()
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                rank = lit_ranks.get((r, c))
                if rank is None:
                    t.append(ch, DIM_GREEN)
                elif rank > head - 1:
                    t.append(ch, WHITE)                       # current head
                elif rank > head - 4:
                    t.append(ch, AMBER)                       # trailing charge
                else:
                    t.append(ch, ACCENT)                      # wired
            t.append("\n")
        milli = int(50 + _h(frame // 2) * 20)
        t.append(Text.assemble(("⚡ ", AMBER if (frame // 2) % 2 else MUTED),
                               ("CURRENT ", MUTED), (f"{milli} mA", TEXT)))
        return Group(t)


class VBreathingPDA(Variant):
    name = "Breathing PDA"

    """The whole screen inhales and exhales while cells lock in softly;
    a pulse ring expands with each breath."""

    def render(self, progress, frame):
        phase = math.sin(frame * 0.12)
        bright = phase > 0.2
        cells = _hash_order_cells()
        visited = int(progress * len(cells))
        lit = set(cells[:visited])
        t = Text()
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                if (r, c) in lit:
                    t.append(ch, ACCENT if bright else SOFT_GREEN)
                else:
                    t.append(ch, DIM_GREEN)
            t.append("\n")
        ring = "○◎◉"[(frame // 4) % 3] if phase > 0 else "·"
        t.append(Text.assemble(((ring + " "), AMBER),
                               ("inhaling…", MUTED) if phase > 0
                               else ("exhaling…", MUTED)))
        return Group(t)


class VTVStatic(Variant):
    name = "TV Static Tune"

    """Analog detune: static everywhere, a clarity wave sweeps in and the
    picture locks behind it. Signal meter climbs."""

    def render(self, progress, frame):
        front = progress * WIDTH
        t = Text()
        for r in range(ROWS):
            for c in range(WIDTH):
                ch = _char(r, c)
                if _is_blank(r, c):
                    t.append(" ")
                    continue
                i = r * WIDTH + c
                d = front - c
                if d > 1:
                    t.append(ch, ACCENT)                       # tuned in
                elif d > 0:
                    t.append(ch, WHITE)                        # lock edge
                else:
                    g = GLYPHS[int(_h(i, salt=frame) * len(GLYPHS))]
                    t.append(g, MUTED)                         # static
            t.append("\n")
        sig = "▂▄▆█"
        lvl = int(progress * 4)
        t.append(Text.assemble(("SIGNAL ", MUTED),
                               (sig[:lvl] if lvl else "▁", AMBER),
                               ("  " + ("LOCKED" if progress > 0.99 else "tuning…"),
                                ACCENT if progress > 0.99 else MUTED)))
        return Group(t)


class VFlipCountdown(Variant):
    name = "Flip Countdown"

    """A mechanical counter flips 10 → 0; every tick locks another slice of
    the art. Zero flashes and the screen goes READY."""

    DIGITS = {                      # 3-row block digits
        '0': ("▛▀▜", "▌ ▐", "▙▄▟"),
        '1': (" ▐ ", " █ ", "▄█▄"),
        '2': ("▛▀▀", "▄▄▐", "▀▀▛"),
        '3': ("▛▀▀", " ▀▀▐", "▄▄▄"),
        '4': ("▌ ▐", "▙▀▀", "  ▐"),
        '5': ("▀▀▛", "▄▄▌", "▄▄▐"),
        '6': ("▀▀▛", "▌▄▄", "▙▄▟"),
        '7': ("▛▀▀", "  ▐", "  ▐"),
        '8': ("▛▀▜", "▣▣▣", "▙▄▟"),
        '9': ("▛▀▜", "▙▀▀", "  ▐"),
    }

    def render(self, progress, frame):
        count = max(0, 10 - int(progress * 10))
        flipping = (progress * 10) % 1 < 0.12 and progress < 0.999
        art = _classic_fill(min(1.0, progress))
        # digit panel beside the art (handles 1-2 digits)
        digit_rows = [self.DIGITS[d] for d in str(count)]
        rows = [ " ".join(dr[i] for dr in digit_rows) for i in range(3) ]
        panel_lines = []
        flash = progress >= 0.999 and (frame // 2) % 2 == 0
        style = AMBER if flipping else (WHITE if flash else ACCENT)
        for i in range(3):
            panel_lines.append(Text(rows[i], style))
        art_lines = art.plain.split("\n")
        t = Text()
        for r in range(ROWS):
            t.append(art_lines[r].ljust(WIDTH + 3),
                     ACCENT if art_lines[r].strip() else "")
            if r in (1, 2, 3):
                t.append(panel_lines[r - 1])
            t.append("\n")
        label = "■ GO ■" if flash else f"T-{count}"
        t.append(Text.assemble(("FLIP ", MUTED), (label, style)))
        return Group(t)


# kept first (user's round-1 picks, in their order), then the new batch
VARIANTS = [
    VClassicFill(),      # 1
    VRadialBloom(),      # 2  (was 3)
    VGeigerTicks(),      # 3  (was 4)
    VMatrixRain(),       # 4  (was 6)
    VSinePulse(),        # 5  (was 8)
    VCRTPowerOn(),       # 6  (was 9)
    VBootLog(),          # 7  (was 10)
    VPowerFault(),       # 8  new
    VDustWind(),         # 9  new
    VOscilloscope(),     # 10 new
    VCipherDecrypt(),    # 11 new
    VZoneDawn(),         # 12 new
    VThermalSweep(),     # 13 new
    VCircuitCurrent(),   # 14 new
    VBreathingPDA(),     # 15 new
    VTVStatic(),         # 16 new
    VFlipCountdown(),    # 17 new
]


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
