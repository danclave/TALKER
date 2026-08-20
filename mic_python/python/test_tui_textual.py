# test_tui_textual.py - Textual TUI flows via Pilot (real app loop)
import asyncio
import logging

logging.getLogger().setLevel(logging.INFO)  # main.py does this in production

from tui import MicApp, AudioSettingsModal
from settings import load_settings


def fresh():
    st = load_settings()
    st["language"] = "en"
    st["vosk_model_overrides"] = {}
    st["custom_models"] = []
    return st


async def boot(app, pilot, timeout=40.0):
    """Wait out the loading screen (and optionally wizard) so flows start
    on an interactive screen."""
    import time as _t
    deadline = _t.time() + timeout
    while _t.time() < deadline:
        name = type(app.screen).__name__
        if name == "LoadingScreen":
            await pilot.pause(0.25)
            continue
        if name == "Wizard" and getattr(app, "_wizard", False):
            return True   # wizard is the expected interactive state
        if name == "Wizard":
            await pilot.pause(0.25)
            continue
        return True
    return False


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
        assert await boot(app, pilot)
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
        assert await boot(app, pilot)
        await pilot.press("4")
        assert app.current_view == "language"
        await pilot.click("#lang-filter")
        await pilot.press("r", "u")
        app._select_language("ru")
        await pilot.pause()
        assert st["language"] == "ru", st
        modal = app.screen
        assert type(modal).__name__ == "ModelPickModal"
        model_list = modal.query_one("#model-pick-list")
        model_list.focus()
        model_list.highlighted = 1
        await pilot.pause()
        model_list.action_select()
        await pilot.pause(0.4)
        assert st["vosk_model_overrides"].get("ru") == "vosk-model-small-ru-0.22", st
        assert app._dirty
        assert "unsaved" in str(app._setup_strip())
    print("FLOW 1 OK: language order + BIG-only tags + ru override + unsaved")


async def flow_gemini():
    st = fresh()
    st["provider"] = "gemini_proxy"
    app = MicApp(st)
    async with app.run_test(size=(110, 32)) as pilot:
        assert await boot(app, pilot)
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
        assert await boot(app, pilot)
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
            assert await boot(app, pilot)
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
    import shutil
    from pathlib import Path
    import models_manager
    # ensure at least one deletable vosk entry exists (user may have wiped
    # the cache - the flow only needs something selectable + cancelable)
    fake = models_manager.VOSK_DIR / "vosk-model-small-zz-test-fake"
    created = False
    if not models_manager.list_vosk_models():
        fake.mkdir(parents=True, exist_ok=True)
        (fake / "conf").write_text("fake", encoding="utf-8")
        created = True
    try:
        st = fresh()
        app = MicApp(st)
        async with app.run_test(size=(110, 32)) as pilot:
            assert await boot(app, pilot)
            await pilot.press("8")
            assert app.current_view == "manager"
            app.query_one("#mgr-vosk").highlighted = 0
            await pilot.pause()
            before = len(models_manager.list_vosk_models())
            app._mgr_delete()
            await pilot.pause()
            assert type(app.screen).__name__ == "ConfirmModal"
            await pilot.click("#confirm-no")
            await pilot.pause()
            after = len(models_manager.list_vosk_models())
            assert before == after, "cancel must not delete"
    finally:
        if created:
            shutil.rmtree(fake, ignore_errors=True)
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
            assert await boot(app, pilot)
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
            # heard panel + history filled after finish (press Stop directly -
            # the button row may be below the fold at this terminal size)
            app.query_one("#test-stop").press()
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
        assert await boot(app, pilot)
        # provider card opens a POPUP (no navigation), pick second entry
        await pilot.click("#card-provider")
        await pilot.pause()
        assert app.current_view == "home", "card must not navigate"
        assert type(app.screen).__name__ == "ProviderPickModal"
        prov_list = app.screen.query_one("#pick-provider-list")
        prov_list.highlighted = 1
        await pilot.pause()
        prov_list.action_select()
        await pilot.pause(0.5)
        assert st["provider"] == "gemini_proxy", st["provider"]
        assert type(app.screen).__name__ != "ProviderPickModal"
        # language card popup: search + pick German
        await pilot.click("#card-language")
        await pilot.pause()
        assert type(app.screen).__name__ == "LanguagePickModal"
        modal = app.screen
        inp = modal.query_one("#pick-lang-filter")
        inp.focus()
        for ch in "ger":
            await pilot.press(ch)
            await pilot.pause(0.2)
        await pilot.pause(0.3)
        lang_list = modal.query_one("#pick-lang-list")
        lang_list.highlighted = 0
        await pilot.pause()
        lang_list.action_select()
        await pilot.pause(0.5)
        assert st["language"] == "de", st["language"]
        # model card: whisper provider -> WhisperPickModal
        st["provider"] = "whisper_local"
        app._refresh_dashboard()
        await pilot.click("#card-model")
        await pilot.pause()
        assert type(app.screen).__name__ == "WhisperPickModal"
        wlist = app.screen.query_one("#pick-whisper-list")
        wlist.highlighted = 1  # base
        await pilot.pause()
        wlist.action_select()
        await pilot.pause(0.5)
        assert st["whisper_model"] == "base", st["whisper_model"]
        # escape from a pane still returns home
        await pilot.press("3")
        await pilot.pause()
        assert app.current_view == "provider"
        await pilot.press("escape")
        await pilot.pause()
        assert app.current_view == "home"
        assert app.query_one("#nav").index == 0
    print("FLOW 7 OK: dashboard popups select+close + escape-home")


async def flow_log_pane():
    import logging as _logging
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(110, 32)) as pilot:
        assert await boot(app, pilot)
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


class _FakeMonitor:
    """Headless stand-in for recorder.AudioMonitor - no native audio."""

    def __init__(self, *a, **k):
        self.playback = bool(k.get("playback", False))
        self._level = 120.0

    def start(self):
        pass

    def stop(self):
        pass

    def get_level(self):
        return self._level

    def is_clipping(self):
        return False

    def set_playback(self, enabled):
        self.playback = bool(enabled)


def patch_monitor(modal_cls):
    """Replace the modal's real monitor with the fake (no PortAudio in tests)."""
    modal_cls._ensure_monitor = lambda self: setattr(
        self, "_monitor", _FakeMonitor(playback=self.settings.get("monitor_live")))


async def flow_wizard_audio_and_details():
    st = fresh()
    # --- wizard on first run: full stepped flow language->provider->confirm ---
    app = MicApp(st, wizard=True)
    async with app.run_test(size=(110, 32)) as pilot:
        assert await boot(app, pilot)
        assert type(app.screen).__name__ == "Wizard"
        wizard = app.screen
        # step 1: language - filter to German, Enter-select advances
        lang_filter = wizard.query_one("#wizard-lang-filter")
        lang_filter.focus()
        for ch in "ger":
            await pilot.press(ch)
            await pilot.pause(0.2)
        await pilot.pause(0.3)
        lang_list = wizard.query_one("#wizard-lang-list")
        lang_list.focus()
        lang_list.highlighted = 0
        await pilot.pause()
        lang_list.action_select()
        await pilot.pause(0.4)
        assert wizard.step == 1, f"expected provider step, at {wizard.step}"
        # step 2: provider - pick gemini (index 1), Enter advances
        prov_list = wizard.query_one("#wizard-provider-list")
        prov_list.focus()
        prov_list.highlighted = 1
        await pilot.pause()
        prov_list.action_select()
        await pilot.pause(0.4)
        assert wizard.step == 2, f"expected summary step, at {wizard.step}"
        # summary shows picks; Finish dismisses with the result
        summary = str(wizard.query_one("#wizard-summary").render())
        assert "German" in summary and "gemini" in summary.lower(), summary[:120]
        wizard.query_one("#wizard-next").press()
        await pilot.pause(0.5)
        assert type(app.screen).__name__ != "Wizard"
        assert st["language"] == "de" and st["provider"] == "gemini_proxy", \
            (st["language"], st["provider"])
    # --- wizard Esc still skips on a fresh boot ---
    app = MicApp(fresh(), wizard=True)
    async with app.run_test(size=(110, 32)) as pilot:
        assert await boot(app, pilot)
        assert type(app.screen).__name__ == "Wizard"
        await pilot.press("escape")
        await pilot.pause()
        assert type(app.screen).__name__ != "Wizard"
        assert app.current_view == "home"
    # --- audio settings modal: threshold tuner + device default ---
    st2 = fresh()
    app = MicApp(st2)
    async with app.run_test(size=(110, 32)) as pilot:
        assert await boot(app, pilot)
        await pilot.press("2")  # Radio Check
        assert app.current_view == "test"
        # no inline device list anymore - it lives in the modal now
        from textual.css.query import NoMatches
        try:
            app.query_one("#device-list")
            raise AssertionError("device list must not be inline anymore")
        except NoMatches:
            pass
        app.query_one("#audio-open").press()
        await pilot.pause(0.4)
        assert type(app.screen).__name__ == "AudioSettingsModal"
        modal = app.screen
        for _ in range(5):        # 1000 + 5*250 = 2250
            modal.query_one("#thr-up").press()
            await pilot.pause(0.05)
        for _ in range(11):       # 2250 - 11*250 = clamp at 100... 2250-2750 -> 100
            modal.query_one("#thr-down").press()
            await pilot.pause(0.05)
        assert st2["silence_level"] == 100, st2["silence_level"]
        for _ in range(4):        # 100 + 1000 = 1100... 100+4*250=1100? no: 100+1000=1100
            modal.query_one("#thr-up").press()
            await pilot.pause(0.05)
        assert st2["silence_level"] == 1100, st2["silence_level"]
        thr = str(modal.query_one("#thr-val").render())
        assert "1100" in thr, thr
        modal.query_one("#audio-done").press()
        await pilot.pause(0.3)
        assert type(app.screen).__name__ != "AudioSettingsModal"
        # --- provider detail panel reacts to highlight ---
        await pilot.press("3")
        app.query_one("#provider-list").highlighted = 1
        await pilot.pause(0.3)
        detail = str(app.query_one("#provider-detail").render())
        assert "proxy" in detail.lower() and "gemini" in detail.lower(), detail[:120]
    print("FLOW 11 OK: stepped wizard (lang->provider->confirm) + skip + audio modal + provider detail")


async def flow_boot_timing():
    """Loading screen paints immediately; heavy init advances the fill."""
    import time as _t
    from tui import MicApp as MA
    st = fresh()
    app = MA(st)
    async with app.run_test(size=(110, 32)) as pilot:
        # within a short window the loader must be up with a step label
        deadline = _t.time() + 5
        seen_loader = False
        while _t.time() < deadline:
            if type(app.screen).__name__ == "LoadingScreen":
                seen_loader = True
                break
            await pilot.pause(0.05)
        assert seen_loader, "loader must show immediately"
        loader = app.screen
        label = str(loader.query_one("#load-step").render())
        assert "..." in label, label
        # eased fill reaches target after steps complete (boot waits it out)
        assert await boot(app, pilot)
        assert loader.target == 1.0
    print("FLOW 12 OK: loading screen paints + eased fill completes")


async def flow_audio_modal_gain_and_playback():
    st2 = fresh()
    app = MicApp(st2)
    async with app.run_test(size=(110, 32)) as pilot:
        assert await boot(app, pilot)
        await pilot.press("2")
        app.query_one("#audio-open").press()
        await pilot.pause(0.4)
        modal = app.screen
        assert type(modal).__name__ == "AudioSettingsModal"
        # gain: 1.0 -> 3.0 via three + presses (0.5 steps)
        for _ in range(4):        # clamp check: 1.0+4*0.5=3.0 valid
            modal.query_one("#gain-up").press()
            await pilot.pause(0.05)
        assert st2["mic_gain"] == 3.0, st2["mic_gain"]
        modal.query_one("#gain-down").press()
        await pilot.pause(0.05)
        assert st2["mic_gain"] == 2.5, st2["mic_gain"]
        gain_label = str(modal.query_one("#gain-val").render())
        assert "2.5" in gain_label, gain_label
        # toggles flip labels and settings, off by default
        assert st2["monitor_live"] is False and st2["playback_after"] is False
        modal.query_one("#toggle-live").press()
        modal.query_one("#toggle-playback").press()
        await pilot.pause(0.1)
        assert st2["monitor_live"] is True and st2["playback_after"] is True
        live_label = str(modal.query_one("#toggle-live").render())
        assert "ON" in live_label, live_label
        modal.query_one("#toggle-live").press()
        await pilot.pause(0.05)
        assert st2["monitor_live"] is False
        modal.query_one("#audio-done").press()
        await pilot.pause(0.3)
        assert type(app.screen).__name__ != "AudioSettingsModal"
        # play-last button exists and stays disabled without a recording
        assert app.query_one("#test-play").disabled
    print("FLOW 13 OK: audio modal gain + hear-yourself toggles + play button")


async def flow_small_terminal_layout():
    """60x20 terminal: audio modal and radio check must stay usable."""
    from textual.containers import VerticalScroll as _VS
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(60, 20)) as pilot:
        assert await boot(app, pilot)
        # audio modal opens without layout errors, Done exists inside a
        # scrollable body, device list capped
        await pilot.press("2")
        app.query_one("#audio-open").press()
        await pilot.pause(0.4)
        assert type(app.screen).__name__ == "AudioSettingsModal"
        modal = app.screen
        done = modal.query_one("#audio-done")
        scroll_parent = done.parent
        while scroll_parent is not None and not isinstance(scroll_parent, _VS):
            scroll_parent = scroll_parent.parent
        assert scroll_parent is not None, "modal body must be a VerticalScroll"
        dev = modal.query_one("#audio-devices")
        # rendered height must be capped (<=8 rows) even with many devices
        assert dev.container_size.height <= 8, dev.container_size
        modal.query_one("#audio-done").press()
        await pilot.pause(0.3)
        # radio check pane: full scroll reaches the last control (not stuck
        # behind the footer)
        pane = app.query_one("#test", _VS)
        pane.scroll_to(y=pane.max_scroll_y, animate=False)
        await pilot.pause(0.2)
        last_btn = app.query_one("#audio-open")
        region = last_btn.region
        view = pane.container_size.height
        assert region.y + region.height <= pane.scroll_offset.y + view + 2, \
            (region, pane.scroll_offset, view)
    print("FLOW 14 OK: 60x20 modal scrollable + device list capped + pane bottom reachable")


async def flow_progress_reporting():
    st = fresh()
    app = MicApp(st)
    async with app.run_test(size=(110, 32)) as pilot:
        assert await boot(app, pilot)
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
    await flow_boot_timing()
    await flow_audio_modal_gain_and_playback()
    await flow_small_terminal_layout()
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
            assert await boot(app, pilot)
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
    patch_monitor(AudioSettingsModal)  # headless: no native audio in Pilot runs
    asyncio.run(main())
