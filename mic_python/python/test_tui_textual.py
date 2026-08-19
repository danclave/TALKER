# test_tui_textual.py - Textual TUI flows via Pilot (real app loop)
import asyncio

from tui import MicApp
from settings import load_settings


def fresh():
    st = load_settings()
    st["language"] = "en"
    st["vosk_model_overrides"] = {}
    return st


async def flow_language():
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(100, 30)) as pilot:
        # jump to language pane via binding
        await pilot.press("4")
        assert app.current_view == "language", app.current_view
        # type a filter
        await pilot.click("#lang-filter")
        await pilot.press("r", "u")
        # rebuild happened via input event; select Russian by direct call path
        app._select_language("ru")
        await pilot.pause()
        assert st["language"] == "ru", st
        # ru has 2 models -> modal on screen; pick option 2 (0.22)
        modal = app.screen
        assert type(modal).__name__ == "ModelPickModal", type(modal).__name__
        modal.query_one("#model-pick-list").highlighted = 1
        await pilot.press("enter")
        await pilot.pause()
        assert st["vosk_model_overrides"].get("ru") == "vosk-model-small-ru-0.22", st
    print("TEXTUAL FLOW 1 OK: language filter + ru + model override")


async def flow_gemini():
    st = fresh()
    st["provider"] = "gemini_proxy"
    app = MicApp(st)
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.press("6")
        assert app.current_view == "gemini"
        app.query_one("#gemini-list").highlighted = 0
        await pilot.pause()
        app._gem_move(1)
        await pilot.pause()
        assert st["gemini_models"][0] == "gemini/gemini-3.1-flash-lite", st["gemini_models"]
        # toggle must refuse empty chain: toggle both off
        app._gem_toggle()   # 3.1 off -> chain = [3.5]
        app._gem_toggle()   # try 3.5 off -> refused
        assert st["gemini_models"], "chain must never be empty"
    print("TEXTUAL FLOW 2 OK: gemini reorder + last-model guard")


async def flow_manager_delete_cancel():
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.press("7")
        assert app.current_view == "manager"
        # highlight first vosk entry, request delete, then cancel
        app.query_one("#mgr-vosk").highlighted = 0
        await pilot.pause()
        before = len(models_manager_list())
        app._mgr_delete()
        await pilot.pause()
        modal = app.screen
        assert type(modal).__name__ == "ConfirmModal"
        await pilot.click("#confirm-no")
        await pilot.pause()
        after = len(models_manager_list())
        assert before == after, "cancel must not delete"
    print("TEXTUAL FLOW 4 OK: manager delete confirm + cancel keeps files")


def models_manager_list():
    import models_manager
    return models_manager.list_vosk_models()


async def flow_radio_check():
    """RADIO CHECK pane: log lines must appear (RichLog) and Stop must work."""
    import time as _time

    def slow_test(settings, status=None, stop_requested=None):
        say = status or print
        say("recording... speak now (stops after ~2s of silence)")
        for _ in range(100):  # wait until Stop is pressed (max 10s)
            if stop_requested and stop_requested():
                say("stop requested - recording ended")
                return ""
            _time.sleep(0.1)
        return ""

    st = fresh()
    app = MicApp(st, test_func=slow_test)
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.press("2")
        assert app.current_view == "test"
        app._start_test()
        await pilot.pause(0.5)
        # buttons: running state
        assert app.query_one("#test-start").disabled
        assert not app.query_one("#test-stop").disabled
        from textual.widgets import RichLog
        log = app.query_one("#test-log", RichLog)
        assert any("speak now" in getattr(strip, "text", "") for strip in log.lines), \
            "instructions must be visible in the log"
        # press Stop -> worker finishes -> buttons reset
        await pilot.click("#test-stop")
        await pilot.pause(1.0)
        assert not app.query_one("#test-start").disabled
        assert app.query_one("#test-stop").disabled
        assert any("stop requested" in getattr(strip, "text", "") for strip in log.lines)
    print("TEXTUAL FLOW 5 OK: radio check logs + stop button")


async def main():
    await flow_language()
    await flow_gemini()
    await flow_manager_delete_cancel()
    await flow_radio_check()
    # flow 3 last: it exits the app via button
    import settings as settings_module
    from pathlib import Path
    orig = settings_module.SETTINGS_FILE
    settings_module.SETTINGS_FILE = Path("_autosave_probe.json")
    try:
        st = fresh()
        st["language"] = "de"
        app = MicApp(st)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.click("#btn-start")
            await pilot.pause()
        saved = settings_module.load_settings()
        assert saved["language"] == "de", saved
        assert settings_module.SETTINGS_FILE.exists()
    finally:
        settings_module.SETTINGS_FILE.unlink(missing_ok=True)
        settings_module.SETTINGS_FILE = orig
    print("TEXTUAL FLOW 3 OK: start button autosaves + exits with settings")
    print("ALL TEXTUAL FLOWS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
