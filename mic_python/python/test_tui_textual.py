# test_tui_textual.py - Textual TUI flows via Pilot (real app loop)
import asyncio
import logging

logging.getLogger().setLevel(logging.INFO)  # main.py does this in production

from tui import MicApp
from settings import load_settings


def fresh():
    st = load_settings()
    st["language"] = "en"
    st["vosk_model_overrides"] = {}
    st["custom_models"] = []
    return st


async def flow_defaults():
    """Factory defaults: whisper small recommended; custom provider present."""
    import settings as s
    st = dict(s.DEFAULT_SETTINGS)
    assert st["provider"] == "whisper_local", st
    assert st["whisper_model"] == "small", st
    assert list(s.PROVIDERS)[0] == "whisper_local"
    assert "custom_proxy" in s.PROVIDERS
    assert "LAST RESORT" in s.WHISPER_MODELS["tiny"]
    assert "RECOMMENDED" in s.WHISPER_MODELS["small"]
    assert "provider/modelname" in s.PROVIDERS["custom_proxy"]
    print("DEFAULTS OK: whisper default, custom provider, guidance wording")


async def flow_language():
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(110, 32)) as pilot:
        # --- ordering: pinned, then whisper-supported, then vosk-only ---
        options = app._language_options("")
        ids = [getattr(o, "id", "") for o in options]
        lang_ids = [i[5:] for i in ids if i.startswith("lang:")]
        assert lang_ids[:6] == ["en", "en-gb", "ru", "uk", "pl", "es"], lang_ids[:6]
        vosk_only = [c for c in lang_ids if c in ("eo", "ky")]
        assert lang_ids[-2:] == ["eo", "ky"], f"vosk-only must be last: {lang_ids[-4:]}"
        assert len(vosk_only) == 2
        # first non-pinned entry must be whisper-capable
        assert __import__("languages").whisper_supported(lang_ids[6]), lang_ids[6]
        # --- BIG tag only on big models ---
        el_label = next(o.prompt for o, i in zip(options, ids) if i == "lang:el")
        assert "1063" in el_label and "BIG" in el_label, el_label
        ru_label = next(o.prompt for o, i in zip(options, ids) if i == "lang:ru")
        assert "39" not in ru_label, f"small vosk size must not be shown: {ru_label}"
        assert "whisper + vosk" in ru_label
        # --- selection flow as before ---
        await pilot.press("4")
        assert app.current_view == "language"
        await pilot.click("#lang-filter")
        await pilot.press("r", "u")
        app._select_language("ru")
        await pilot.pause()
        assert st["language"] == "ru", st
        modal = app.screen
        assert type(modal).__name__ == "ModelPickModal"
        modal.query_one("#model-pick-list").highlighted = 1
        await pilot.press("enter")
        await pilot.pause()
        assert st["vosk_model_overrides"].get("ru") == "vosk-model-small-ru-0.22", st
        assert app._dirty
        assert "unsaved" in str(app._setup_strip())
    print("FLOW 1 OK: language order + BIG-only tags + ru override + unsaved")


async def flow_gemini():
    st = fresh()
    st["provider"] = "gemini_proxy"
    app = MicApp(st)
    async with app.run_test(size=(110, 32)) as pilot:
        await pilot.press("6")
        assert app.current_view == "gemini"
        app.query_one("#gemini-list").highlighted = 0
        await pilot.pause()
        app._gem_move(1)
        await pilot.pause()
        assert st["gemini_models"][0] == "gemini/gemini-3.1-flash-lite", st["gemini_models"]
        app._gem_toggle()
        app._gem_toggle()
        assert st["gemini_models"], "chain must never be empty"
    print("FLOW 2 OK: gemini reorder + last-model guard")


async def flow_custom_models():
    st = fresh()
    st["provider"] = "custom_proxy"
    app = MicApp(st)
    async with app.run_test(size=(110, 32)) as pilot:
        await pilot.press("7")
        assert app.current_view == "custom"
        # bad format rejected
        app.query_one("#custom-input").value = "no-slash-model"
        app._custom_add()
        await pilot.pause()
        assert not st["custom_models"], "must reject bad format"
        # good format added via input submit
        app.query_one("#custom-input").value = "gemini/gemini-3.5-flash-lite"
        app._custom_add()
        await pilot.pause()
        assert st["custom_models"] == ["gemini/gemini-3.5-flash-lite"]
        # second model + reorder
        app.query_one("#custom-input").value = "openai/gpt-4o-audio-preview"
        app._custom_add()
        await pilot.pause()
        app.query_one("#custom-list").highlighted = 1
        app._custom_move(-1)
        await pilot.pause()
        assert st["custom_models"][0] == "openai/gpt-4o-audio-preview", st["custom_models"]
        # delete
        app.query_one("#custom-list").highlighted = 0
        app._custom_delete()
        await pilot.pause()
        assert st["custom_models"] == ["gemini/gemini-3.5-flash-lite"]
    print("FLOW 3 OK: custom models add/format-guard/reorder/delete")


async def flow_custom_start_guard():
    import settings as settings_module
    from pathlib import Path
    orig = settings_module.SETTINGS_FILE
    settings_module.SETTINGS_FILE = Path("_guard_probe.json")
    try:
        st = fresh()
        st["provider"] = "custom_proxy"
        st["custom_models"] = []
        app = MicApp(st)
        async with app.run_test(size=(110, 32)) as pilot:
            app.action_start()   # must NOT exit: empty chain
            await pilot.pause()
            assert app.is_running, "empty custom chain must block start"
            assert app.current_view == "custom"
            st["custom_models"] = ["gemini/gemini-3.5-flash-lite"]
            app.action_start()   # now it exits with settings
            await pilot.pause()
            assert not app.is_running
            assert app.return_value is st
    finally:
        settings_module.SETTINGS_FILE.unlink(missing_ok=True)
        settings_module.SETTINGS_FILE = orig
    print("FLOW 4 OK: custom empty-chain start guard")


async def flow_manager_delete_cancel():
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(110, 32)) as pilot:
        await pilot.press("8")
        assert app.current_view == "manager"
        app.query_one("#mgr-vosk").highlighted = 0
        await pilot.pause()
        before = len(models_manager_list())
        app._mgr_delete()
        await pilot.pause()
        assert type(app.screen).__name__ == "ConfirmModal"
        await pilot.click("#confirm-no")
        await pilot.pause()
        assert len(models_manager_list()) == before, "cancel must not delete"
    print("FLOW 5 OK: manager delete confirm + cancel keeps files")


async def flow_radio_check():
    import time as _time

    def slow_test(settings, status=None, stop_requested=None, on_recording=None,
                  on_level=None):
        say = status or print
        say("recording... speak now (stops after ~2s of silence)")
        if on_recording:
            on_recording(True)
        for i in range(100):
            if on_level:
                on_level(30 + (i % 5) * 10, None if i % 3 else 1.5, i * 0.1)
            if stop_requested and stop_requested():
                say("stop requested - recording ended")
                break
            _time.sleep(0.05)
        if on_recording:
            on_recording(False)
        say("heard: test sentence for the log")
        return "test sentence for the log"

    st = fresh()
    import providers
    orig_prepare = providers.prepare_model
    providers.prepare_model = lambda s, report=None: True
    try:
        app = MicApp(st, test_func=slow_test)
        async with app.run_test(size=(110, 32)) as pilot:
            await pilot.press("2")
            app._start_test()
            await pilot.pause(1.0)
            assert app.query_one("#test-start").disabled
            assert not app.query_one("#test-stop").disabled
            from textual.widgets import RichLog
            log = app.query_one("#test-log", RichLog)
            assert any("speak now" in getattr(strip, "text", "") for strip in log.lines)
            assert app.recording
            assert "on" in app.query_one("#rec-badge").classes
            # level meter updated with bar cells + threshold marker
            meter_text = str(app.query_one("#meter").render())
            assert "|" in meter_text, meter_text
            # heard panel + history filled after finish
            await pilot.click("#test-stop")
            await pilot.pause(1.5)
            assert not app.recording
            assert not app.query_one("#test-start").disabled
            heard = str(app.query_one("#heard-panel").render())
            assert "test sentence for the log" in heard, heard
            assert app._history and "test sentence" in app._history[0][2], app._history
            assert len(app._history) == 1
    finally:
        providers.prepare_model = orig_prepare
    print("FLOW 6 OK: radio check + meter + heard panel + history + stop")


async def flow_dashboard_and_escape():
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(110, 32)) as pilot:
        # dashboard cards navigate (return Home between clicks - cards are
        # only visible there)
        await pilot.click("#card-provider")
        await pilot.pause()
        assert app.current_view == "provider"
        await pilot.press("escape")
        await pilot.click("#card-language")
        await pilot.pause()
        assert app.current_view == "language"
        await pilot.press("escape")
        await pilot.click("#card-model")
        await pilot.pause()
        assert app.current_view == "whisper"  # whisper provider -> whisper pane
        await pilot.press("escape")
        await pilot.pause()
        assert app.current_view == "home"
        # nav list reflects current view
        await pilot.press("3")
        await pilot.pause()
        assert app.query_one("#nav").index == 2
    print("FLOW 7 OK: dashboard cards + escape-home + nav sync")


async def flow_log_pane():
    import logging as _logging
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(110, 32)) as pilot:
        pane = app.query_one("#logpane")
        assert pane.display is False, "log pane starts hidden"
        _logging.getLogger().info("diagnostics test line")
        await pilot.pause(1.0)  # let the ticker drain
        # info alone must NOT auto-open
        assert pane.display is False
        await pilot.press("f12")
        await pilot.pause()
        assert pane.display is True
        from textual.widgets import RichLog
        assert any("diagnostics test line" in getattr(strip, "text", "")
                   for strip in app.query_one("#applog", RichLog).lines)
        await pilot.press("f12")  # close again
        await pilot.pause()
        assert pane.display is False
        _logging.getLogger().error("boom")
        await pilot.pause(1.0)
        assert pane.display is True, "errors must auto-open the pane"
        assert any("boom" in getattr(strip, "text", "")
                   for strip in app.query_one("#applog", RichLog).lines)
    print("FLOW 8 OK: log pane toggle + auto-open on errors")


async def flow_wizard_audio_and_details():
    st = fresh()
    # --- wizard on first run, Esc skips ---
    app = MicApp(st, wizard=True)
    async with app.run_test(size=(110, 32)) as pilot:
        assert type(app.screen).__name__ == "Wizard"
        await pilot.press("escape")
        await pilot.pause()
        assert type(app.screen).__name__ != "Wizard"
        assert app.current_view == "home"
    # --- threshold tuner ---
    app = MicApp(fresh())
    async with app.run_test(size=(110, 32)) as pilot:
        before = st.get("silence_level", 1000)
        app._tune_threshold(250)          # 1000 -> 1250
        app._tune_threshold(-2000)        # 1250 -> clamps at 100
        await pilot.pause()
        assert app.settings["silence_level"] == 100, app.settings
        app._tune_threshold(900)          # 100 -> 1000
        await pilot.pause()
        assert app.settings["silence_level"] == 1000
        thr = str(app.query_one("#thr-val").render())
        assert "1000" in thr, thr
        # --- provider detail panel reacts to highlight ---
        await pilot.press("3")
        app.query_one("#provider-list").highlighted = 1
        await pilot.pause(0.3)
        detail = str(app.query_one("#provider-detail").render())
        assert "proxy" in detail.lower() and "gemini" in detail.lower(), detail[:120]
    print("FLOW 11 OK: wizard skip + threshold tuner + provider detail")


async def flow_progress_reporting():
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(110, 32)) as pilot:
        await pilot.press("2")
        app._test_progress("downloading 'x'", 20, 40)
        await pilot.pause()
        assert app.query_one("#test-progress").progress == 50
        app._test_progress("model ready", None, None)
        await pilot.pause()
        assert app.query_one("#test-progress").progress == 100
        app._test_progress("loading whisper", 0, None)
        await pilot.pause()
    print("FLOW 9 OK: progress bar determinate/done/pulse")


async def main():
    await flow_defaults()
    await flow_language()
    await flow_gemini()
    await flow_custom_models()
    await flow_custom_start_guard()
    await flow_manager_delete_cancel()
    await flow_radio_check()
    await flow_dashboard_and_escape()
    await flow_log_pane()
    await flow_wizard_audio_and_details()
    await flow_progress_reporting()
    # start-autosave last: exits the app
    import settings as settings_module
    from pathlib import Path
    orig = settings_module.SETTINGS_FILE
    settings_module.SETTINGS_FILE = Path("_autosave_probe.json")
    try:
        st = fresh()
        st["language"] = "de"
        app = MicApp(st)
        async with app.run_test(size=(110, 32)) as pilot:
            await pilot.click("#btn-start")
            await pilot.pause()
        saved = settings_module.load_settings()
        assert saved["language"] == "de", saved
    finally:
        settings_module.SETTINGS_FILE.unlink(missing_ok=True)
        settings_module.SETTINGS_FILE = orig
    print("FLOW 10 OK: start button autosaves + exits with settings")
    print("ALL TEXTUAL FLOWS PASSED")


def models_manager_list():
    import models_manager
    return models_manager.list_vosk_models()


if __name__ == "__main__":
    asyncio.run(main())
