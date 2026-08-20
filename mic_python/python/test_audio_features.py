# test_audio_features.py - headless tests for silence arming, gain, playback
# (no real audio device needed: the recorder callback is driven synthetically)
import time
from pathlib import Path

import numpy as np

import recorder as rec


class FakeRecorder(rec.Recorder):
    """Recorder with the InputStream replaced by synthetic frame injection."""

    def start_recording(self, silence_grace_period=0, arm_on_speech=False,
                        no_speech_timeout=10.0):
        # same state setup, without opening a device
        with self._lock:
            self._recording = True
            self._audio_frames = []
            self._silence_start = None
            self._should_stop = False
            self._speech_started = False
            self._clipping = False
        import threading
        threading.Thread(target=self._monitor_silence,
                         args=(silence_grace_period, arm_on_speech,
                               no_speech_timeout), daemon=True).start()

    def inject(self, level: float, seconds: float = 0.1):
        """Feed ~seconds of audio at the given mean level."""
        frames = int(self._rate * seconds)
        data = (np.ones((frames, 1)) * level).astype(np.int16)
        self._audio_callback(data, frames, None, None)

    def stop_recording(self):
        with self._lock:
            if not self._recording:
                return
            self._recording = False
            # skip _save_audio (no device, no file wanted)
        self._should_stop = False


def test_silence_counts_after_speech():
    """arm_on_speech: countdown starts right after speech ends - NOT after
    a fixed grace. Silent wait before speaking must not count."""
    r = FakeRecorder("x", silence_threshold=2.0, silence_level=1000)
    r.start_recording(arm_on_speech=True, no_speech_timeout=30.0)
    try:
        # 3s of silence BEFORE speaking - must not count toward the stop
        for _ in range(30):
            r.inject(10, 0.1)   # quiet
            time.sleep(0.02)
        assert r.get_silence_remaining() is None, \
            "pre-speech silence must not start the countdown"
        assert not r.speech_started()

        # speak 0.3s
        r.inject(3000, 0.3)
        assert r.speech_started(), "loud input must arm speech"

        # go silent; countdown must begin within ~0.2s of the speech ending
        deadline = time.time() + 0.5
        remaining = None
        while time.time() < deadline:
            r.inject(10, 0.1)
            remaining = r.get_silence_remaining()
            if remaining is not None:
                break
            time.sleep(0.02)
        assert remaining is not None, \
            "countdown must start immediately after speech stops"
        assert 1.5 < remaining <= 2.05, remaining
    finally:
        r.stop_recording()
    print("TEST 1 OK: countdown arms on first speech, starts <=0.2s after it ends")


def test_no_speech_timeout():
    """arm_on_speech with nobody talking: stops after no_speech_timeout."""
    r = FakeRecorder("x", silence_threshold=2.0, silence_level=1000)
    t0 = time.time()
    r.start_recording(arm_on_speech=True, no_speech_timeout=1.0)
    while r.is_recording() and time.time() - t0 < 5:
        r.inject(10, 0.1)
        time.sleep(0.05)
    total = time.time() - t0
    assert not r.is_recording(), "must auto-stop when nobody speaks"
    assert 0.8 <= total <= 2.5, total
    print(f"TEST 2 OK: no-speech timeout fired after {total:.1f}s")


def test_fixed_grace_still_works():
    """Classic fixed grace (game path uses grace=0): countdown runs right
    away when quiet."""
    r = FakeRecorder("x", silence_threshold=2.0, silence_level=1000)
    r.start_recording(silence_grace_period=0)
    try:
        deadline = time.time() + 0.5
        remaining = None
        while time.time() < deadline:
            r.inject(10, 0.1)
            remaining = r.get_silence_remaining()
            if remaining is not None:
                break
            time.sleep(0.02)
        assert remaining is not None, "grace=0 must count silence immediately"
    finally:
        r.stop_recording()
    print("TEST 3 OK: grace=0 counts silence immediately (game path intact)")


def test_gain_scales_and_clips():
    """Gain multiplies samples before save; clipping is flagged at the ceiling."""
    r = FakeRecorder("x", gain=4.0)
    quiet = np.full((10, 1), 9000, dtype=np.int16)   # 9000*4 = 36000 > 32767
    r._audio_callback(quiet, 10, None, None)
    saved = r._audio_frames[-1]
    assert saved.max() == 32767, "boosted samples must clamp at int16 max"
    assert r.is_clipping(), "clipping must be flagged"
    # level also reflects the boost (quiet mic reads as loud speech)
    assert r.get_level() >= 20000, r.get_level()

    r2 = FakeRecorder("x", gain=2.0)
    mid = np.full((10, 1), 2000, dtype=np.int16)
    r2._audio_callback(mid, 10, None, None)
    assert r2._audio_frames[-1].max() == 4000, "2x gain must double samples"
    assert not r2.is_clipping()
    print("TEST 4 OK: gain scales samples, clamps + flags clipping")


def test_playback_toggle_and_file():
    """AudioMonitor.set_playback restarts; play_audio_file logs not raises."""
    m = rec.AudioMonitor(playback=False)
    m.set_playback(True)
    assert m.playback is True
    m.set_playback(False)
    assert m.playback is False
    # nonexistent file: must swallow
    rec.play_audio_file("does_not_exist.ogg")
    print("TEST 5 OK: playback toggle + fire-and-forget file playback")


class FakeOutputStream:
    def __init__(self):
        self.stopped = False
        self.closed = False
        self.written = []

    def start(self):
        pass

    def stop(self):
        self.stopped = True

    def close(self):
        self.closed = True

    def write(self, data):
        self.written.append(len(data))


def test_live_echo_reenable():
    """Echo off must TEAR DOWN the output stream so re-enable works.

    Regression: the drain thread's normal exit left _out_stream set, and
    the stale reference blocked _maybe_start_playback forever (echo
    worked exactly once).
    """
    import recorder as rec2
    m = rec2.AudioMonitor(playback=True)
    fake_out = FakeOutputStream()

    # fake the streams (no real audio)
    m._stream = object()
    orig_output = rec2.sd.OutputStream
    rec2.sd.OutputStream = lambda *a, **k: fake_out

    try:
        # pump audio until the drain thread starts
        import numpy as np
        deadline = time.time() + 2
        while m._out_stream is None and time.time() < deadline:
            data = np.ones((1600, 1), dtype=np.int16) * 100
            m._callback(data, 1600, None, None)
            time.sleep(0.02)
        assert m._out_stream is fake_out, "drain must open the output stream"

        # disable: drain thread must close + null the stream
        m.set_playback(False)
        deadline = time.time() + 2
        while m._out_stream is not None and time.time() < deadline:
            time.sleep(0.02)
        assert m._out_stream is None, "stream reference must be cleared"
        assert fake_out.stopped and fake_out.closed, "stream must be closed"

        # re-enable: pumping must open a FRESH stream (the regression)
        m.set_playback(True)
        fake_out_2 = FakeOutputStream()
        rec2.sd.OutputStream = lambda *a, **k: fake_out_2
        deadline = time.time() + 2
        while m._out_stream is None and time.time() < deadline:
            data = np.ones((1600, 1), dtype=np.int16) * 100
            m._callback(data, 1600, None, None)
            time.sleep(0.02)
        assert m._out_stream is fake_out_2, "re-enable must open a NEW stream"
    finally:
        rec2.sd.OutputStream = orig_output
        m.set_playback(False)
        m.stop()
    print("TEST 6 OK: live echo disable tears down stream; re-enable works")


if __name__ == "__main__":
    test_silence_counts_after_speech()
    test_no_speech_timeout()
    test_fixed_grace_still_works()
    test_gain_scales_and_clips()
    test_playback_toggle_and_file()
    test_live_echo_reenable()
    print("ALL AUDIO FEATURE TESTS PASSED")
