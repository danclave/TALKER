# test_tui_textual.py - Textual TUI flows via Pilot (real app loop)
import asyncio

from tui import MicApp
from settings import load_settings


def fresh():
    st = load_settings()
    st["language"] = "en"
    st["vosk_model_overrides"] = {}
    return st


async def flow_defaults():
    """Factory defaults: whisper small recommended, not vosk."""
    import settings as s
    st = dict(s.DEFAULT_SETTINGS)
    assert st["provider"] == "whisper_local", st
    assert st["whisper_model"] == "small", st
    first = list(s.PROVIDERS)[0]
    assert first == "whisper_local", "whisper must be listed first (recommended)"
    assert "lower accuracy" in s.PROVIDERS["vosk_local"]
    print("DEFAULTS OK: whisper small default, vosk demoted with warning")


async def flow_language():
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.press("4")
        assert app.current_view == "language", app.current_view
        await pilot.click("#lang-filter")
        await pilot.press("r", "u")
        app._select_language("ru")
        await pilot.pause()
        assert st["language"] == "ru", st
        modal = app.screen
        assert type(modal).__name__ == "ModelPickModal", type(modal).__name__
        modal.query_one("#model-pick-list").highlighted = 1
        await pilot.press("enter")
        await pilot.pause()
        assert st["vosk_model_overrides"].get("ru") == "vosk-model-small-ru-0.22", st
        # unsaved marker must be visible now
        assert app._dirty, "changing language must mark dirty"
        strip = str(app._setup_strip())
        assert "unsaved" in strip, strip
    print("TEXTUAL FLOW 1 OK: language filter + ru + model override + unsaved marker")


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


async def flow_radio_check():
    """RADIO CHECK: log lines, REC indicator, progress bar, Stop button."""
    import time as _time

    def slow_test(settings, status=None, stop_requested=None, on_recording=None):
        say = status or print
        say("recording... speak now (stops after ~2s of silence)")
        if on_recording:
            on_recording(True)
        for _ in range(100):  # wait until Stop is pressed (max 10s)
            if stop_requested and stop_requested():
                say("stop requested - recording ended")
                break
            _time.sleep(0.1)
        if on_recording:
            on_recording(False)
        say("heard: test sentence for the log")
        return "test sentence for the log"

    st = fresh()
    import providers
    orig_prepare = providers.prepare_model
    providers.prepare_model = lambda s, report=None: True  # skip real model load
    try:
        app = MicApp(st, test_func=slow_test)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.press("2")
            assert app.current_view == "test"
            app._start_test()
            await pilot.pause(1.0)
            assert app.query_one("#test-start").disabled
            assert not app.query_one("#test-stop").disabled
            from textual.widgets import RichLog
            log = app.query_one("#test-log", RichLog)
            assert any("speak now" in getattr(strip, "text", "") for strip in log.lines)
            # REC indicator: reactive must be True while recording
            assert app.recording, "on_recording(True) must set the reactive"
            badge = app.query_one("#rec-badge")
            pane = app.query_one("#test")
            assert "recording" in pane.classes, pane.classes
            assert "on" in badge.classes, badge.classes
            # Stop -> ends -> indicators reset
            await pilot.click("#test-stop")
            await pilot.pause(1.5)
            assert not app.recording
            assert "recording" not in app.query_one("#test").classes
            assert not app.query_one("#test-start").disabled
            assert app.query_one("#test-stop").disabled
            assert any("stop requested" in getattr(strip, "text", "") for strip in log.lines)
    finally:
        providers.prepare_model = orig_prepare
    print("TEXTUAL FLOW 5 OK: radio check logs + REC indicator + stop button")


async def flow_escape_home_and_save():
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.press("4")            # language pane
        assert app.current_view == "language"
        st["language"] = "de"             # simulate an edit
        app._mark_dirty()
        await pilot.pause()
        await pilot.press("escape")       # back home
        assert app.current_view == "home", app.current_view
        assert "unsaved" in str(app._setup_strip())
        # save -> clean
        app.action_save()
        await pilot.pause()
        assert not app._dirty
        assert "unsaved" not in str(app._setup_strip())
    print("TEXTUAL FLOW 6 OK: escape-to-home + unsaved marker + save clears it")


async def flow_progress_reporting():
    """_test_progress drives the bar: determinate %, done state, pulse."""
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.press("2")
        app._test_progress("downloading 'x'", 20, 40)
        await pilot.pause()
        bar = app.query_one("#test-progress")
        assert bar.progress == 50, bar.progress
        app._test_progress("model ready", None, None)
        await pilot.pause()
        assert app.query_one("#test-progress").progress == 100
        app._test_progress("loading whisper", 0, None)
        await pilot.pause()  # pulse must not raise
    print("TEXTUAL FLOW 7 OK: progress bar determinate/done/pulse")


async def main():
    await flow_defaults()
    await flow_language()
    await flow_gemini()
    await flow_manager_delete_cancel()
    await flow_radio_check()
    await flow_escape_home_and_save()
    await flow_progress_reporting()
    # start-autosave last: it exits the app
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
    finally:
        settings_module.SETTINGS_FILE.unlink(missing_ok=True)
        settings_module.SETTINGS_FILE = orig
    print("TEXTUAL FLOW 3 OK: start button autosaves + exits with settings")
    print("ALL TEXTUAL FLOWS PASSED")


def models_manager_list():
    import models_manager
    return models_manager.list_vosk_models()


if __name__ == "__main__":
    asyncio.run(main())
