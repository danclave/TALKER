# Archived: classic keyboard-driven TUI

This is the superseded first TUI (prompt_toolkit + rich, no mouse support).
It is kept as source reference only - it is NOT built into any executable
and receives no further development.

Notes for archaeologists:
- prompt_toolkit's Windows input is a non-blocking poll and its Keys enum
  values use short forms ('c-m' for Enter), both of which caused real
  bugs during development (see git history of tui_old.py).
- The active TUI is ../tui.py (Textual, mouse + keyboard).
- main_old.py was the entry point for the talker_mic_old.exe build.

Everything else in the mic app (providers, settings, tests) is shared and
still maintained in the parent directory.
