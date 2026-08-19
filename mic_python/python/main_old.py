# main_old.py
# entry point for the classic (non-Textual) TUI build: talker_mic_old.exe
# identical service behavior to main.py, only the configuration UI differs

import tui_old

import main

main.TUI_OVERRIDE = tui_old

if __name__ == "__main__":
    main.main()
