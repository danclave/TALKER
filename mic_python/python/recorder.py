import logging
import os
import threading
import time

import numpy as np
import sounddevice as sd
import soundfile as sf


def _clamp_int16(data):
    """Scale-free int16 clamp (gain is applied by the caller)."""
    return np.clip(data, -32768, 32767)


class Recorder:
    def __init__(self, output_file=None, silence_threshold=2.0, silence_level=1000,
                 device=None, gain=1.0):
        """
        Initializes the Recorder.

        :param output_file: Path to save the recorded audio file. If None, a temp file will be used.
        :param silence_threshold: Duration of silence in seconds to stop recording automatically.
        :param silence_level: Audio level considered as silence (lower means more sensitive).
        :param device: Input device index (None = system default).
        :param gain: Software mic gain multiplier (1.0 = unchanged).
        """
        self.output_file = output_file or self._generate_temp_filename()
        self.silence_threshold = silence_threshold
        self.silence_level = silence_level
        self.device = device
        self.gain = float(gain)
        self._recording = False
        self._audio_frames = []
        self._lock = threading.Lock()
        self._silence_start = None
        self._channels = 1
        self._rate = 16000  # Sampling rate
        self._dtype = 'int16'
        self._stream = None
        self._should_stop = False  # Flag to indicate recording should stop
        self._last_audio_level = None
        self._speech_started = False   # first-speech arming (test mode)
        self._clipping = False        # boosted samples pinned at int16 max

    def _generate_temp_filename(self):
        temp_dir = os.getenv('TEMP', '/tmp')
        timestamp = int(time.time())
        return os.path.join(temp_dir, f"recording_{timestamp}.ogg")

    def start_recording(self, silence_grace_period=0, arm_on_speech=False,
                        no_speech_timeout=10.0):
        """
        Starts recording audio from the microphone.

        :param silence_grace_period: Duration in seconds to ignore silence at
            the beginning (classic fixed grace).
        :param arm_on_speech: wait for the first speech before the silence
            countdown may start (radio checks) - silence before you speak
            never counts toward auto-stop.
        :param no_speech_timeout: with arm_on_speech, stop after this many
            seconds total without any speech.
        """
        with self._lock:
            if self._recording:
                logging.info("Already recording.")
                return
            self._recording = True
            self._audio_frames = []
            self._silence_start = None
            self._should_stop = False
            self._speech_started = False
            self._clipping = False

            self._stream = sd.InputStream(samplerate=self._rate,
                                          channels=self._channels,
                                          dtype=self._dtype,
                                          device=self.device,
                                          callback=self._audio_callback)
            self._stream.start()
            logging.info("Recording started.")

        # Start a thread to monitor silence and stop recording
        threading.Thread(target=self._monitor_silence,
                         args=(silence_grace_period, arm_on_speech,
                               no_speech_timeout),
                         daemon=True).start()

    def stop_recording(self):
        """
        Stops recording audio.
        """
        with self._lock:
            if not self._recording:
                logging.info("Not currently recording.")
                return
            self._recording = False
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

            self._save_audio()
            logging.info("Recording stopped.")

    def is_recording(self):
        """
        Returns True if currently recording, else False.
        """
        with self._lock:
            return self._recording

    def get_level(self):
        """Current raw mic level (mean abs int16 amplitude, pre-gain), or None."""
        with self._lock:
            return self._last_audio_level

    def is_clipping(self):
        """True when the last window had boosted samples at the int16 ceiling."""
        with self._lock:
            return self._clipping

    def speech_started(self):
        with self._lock:
            return self._speech_started

    def get_silence_remaining(self):
        """Seconds until auto-stop if input stays silent, else None."""
        with self._lock:
            if self._silence_start is None:
                return None
            return max(0.0, self.silence_threshold - (time.time() - self._silence_start))

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback function for the InputStream.
        """
        if status:
            logging.debug("Stream status: %s", status)

        audio_data = indata.copy()

        # level BEFORE gain so the threshold keeps its absolute meaning for
        # unamplified mic sensitivity... but gain should make quiet mics
        # count as speech, so level is measured AFTER gain (consistent with
        # what the recognizer and the user hear).
        scaled = audio_data * self.gain
        self._clipping = bool(np.any(np.abs(scaled) >= 32767))
        audio_data = _clamp_int16(scaled).astype(np.int16)

        self._audio_frames.append(audio_data)

        # Calculate audio level
        audio_level = float(np.abs(audio_data).mean())

        with self._lock:
            self._last_audio_level = audio_level
            if audio_level >= self.silence_level:
                self._speech_started = True

    def _monitor_silence(self, silence_grace_period=0, arm_on_speech=False,
                         no_speech_timeout=10.0):
        """
        Monitors audio levels and stops recording after silence is detected.
        """
        start_time = time.time()
        while True:
            with self._lock:
                if not self._recording:
                    break
                audio_level = self._last_audio_level

            if audio_level is not None:
                in_fixed_grace = time.time() - start_time < silence_grace_period
                not_yet_spoken = arm_on_speech and not self._speech_started
                if in_fixed_grace or not_yet_spoken:
                    self._silence_start = None  # countdown may not run yet
                elif audio_level < self.silence_level:
                    if self._silence_start is None:
                        self._silence_start = time.time()
                    elif (time.time() - self._silence_start) >= self.silence_threshold:
                        self._should_stop = True
                else:
                    self._silence_start = None

                if (arm_on_speech and not_yet_spoken and
                        time.time() - start_time >= no_speech_timeout):
                    logging.info("No speech detected within %.1fs - stopping.",
                                 no_speech_timeout)
                    self._should_stop = True

            if self._should_stop:
                self.stop_recording()
                break

            time.sleep(0.1)

    def _save_audio(self):
        """
        Saves the recorded audio to the output file in OGG format.
        """
        if not self._audio_frames:
            logging.warning("No audio captured - nothing to save.")
            return
        # Concatenate all frames
        audio_data = np.concatenate(self._audio_frames, axis=0)

        # Write to OGG file
        sf.write(self.output_file, audio_data, self._rate, format='OGG', subtype='VORBIS')

    def __del__(self):
        """
        Ensures resources are cleaned up.
        """
        if getattr(self, "_stream", None):
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
        try:
            sd.stop()
        except Exception:
            pass


class AudioMonitor:
    """Always-on mic monitor for live UI feedback and optional live playback.

    Owns a tiny InputStream; exposes get_level()/is_clipping() like Recorder
    so the UI can share rendering code. When playback=True, input is echoed
    to the default output after a short buffering delay (headphones
    recommended - speakers feed back into the mic). Safe to stop/restart on
    device or gain changes.
    """

    RATE = 16000
    CHANNELS = 1
    PLAYBACK_DELAY_S = 0.12   # ring-buffer depth before playback starts

    def __init__(self, device=None, gain=1.0, playback=False):
        self.device = device
        self.gain = float(gain)
        self.playback = bool(playback)
        self._stream = None
        self._out_stream = None
        self._lock = threading.Lock()
        self._level = None
        self._clipping = False
        self._ring = []            # queued np arrays awaiting playback
        self._ring_samples = 0

    def start(self):
        with self._lock:
            if self._stream is not None:
                return
            self._ring = []
            self._ring_samples = 0
            self._out_stream = None
            try:
                self._stream = sd.InputStream(samplerate=self.RATE,
                                              channels=self.CHANNELS,
                                              dtype="int16",
                                              device=self.device,
                                              callback=self._callback)
                self._stream.start()
            except Exception as e:
                logging.warning("AudioMonitor could not open input stream: %s", e)
                self._stream = None

    def stop(self):
        with self._lock:
            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None
            if self._out_stream is not None:
                try:
                    self._out_stream.stop()
                    self._out_stream.close()
                except Exception:
                    pass
                self._out_stream = None
            self._level = None
            self._ring = []
            self._ring_samples = 0

    def set_playback(self, enabled: bool):
        """Toggle live echo; restarts cleanly if needed."""
        if enabled == self.playback:
            return
        self.playback = enabled
        was_running = self._stream is not None
        self.stop()
        if was_running:
            self.start()

    def _callback(self, indata, frames, time_info, status):
        data = indata.copy()
        scaled = data * self.gain
        self._clipping = bool(np.any(np.abs(scaled) >= 32767))
        data = _clamp_int16(scaled).astype(np.int16)

        level = float(np.abs(data).mean())
        with self._lock:
            self._level = level
            if self.playback:
                self._ring.append(data)
                self._ring_samples += len(data)
                self._maybe_start_playback()

    def _maybe_start_playback(self):
        """Called under lock: schedule the echo stream once the ring is deep
        enough, then drain it into the output via RawOutputQueue-style write."""
        if self._out_stream is not None or not self.playback:
            return
        target = int(self.PLAYBACK_DELAY_S * self.RATE)
        if self._ring_samples < target:
            return
        try:
            self._out_stream = sd.OutputStream(samplerate=self.RATE,
                                               channels=self.CHANNELS,
                                               dtype="int16")
            self._out_stream.start()
        except Exception as e:
            logging.warning("AudioMonitor playback stream failed: %s", e)
            self._out_stream = None
            self.playback = False
            self._ring = []
            self._ring_samples = 0
            return
        # flush the buffered audio, then keep the drain on a timer thread
        buffered = np.concatenate(self._ring)
        self._ring = []
        self._ring_samples = 0
        try:
            self._out_stream.write(buffered)
        except Exception as e:
            logging.warning("AudioMonitor playback write failed: %s", e)
        threading.Thread(target=self._drain_playback, daemon=True).start()

    def _drain_playback(self):
        """Pump new input into the output stream (keeps ~the ring delay)."""
        import queue
        pending = queue.Queue()
        with self._lock:
            for chunk in self._ring:
                pending.put(chunk)
        while True:
            with self._lock:
                running = self._out_stream is not None and self.playback
                ring = self._ring
                self._ring = []
                self._ring_samples = 0
            if not running:
                return
            for chunk in ring:
                pending.put(chunk)
            try:
                wrote = False
                while not pending.empty():
                    item = pending.get_nowait()
                    self._out_stream.write(item)
                    wrote = True
                if not wrote:
                    time.sleep(0.02)  # nothing new; brief idle wait
            except Exception as e:
                logging.warning("AudioMonitor playback stopped: %s", e)
                with self._lock:
                    self.playback = False
                    if self._out_stream is not None:
                        try:
                            self._out_stream.stop()
                            self._out_stream.close()
                        except Exception:
                            pass
                        self._out_stream = None
                return

    def get_level(self):
        with self._lock:
            return self._level

    def is_clipping(self):
        with self._lock:
            return self._clipping


def play_audio_file(path, device=None):
    """Play an audio file on the default (or given) output device. Fire-and-
    forget safe: errors are logged, never raised."""
    try:
        data, rate = sf.read(path, dtype="int16", always_2d=True)
        if data.shape[1] > 1:
            data = data.mean(axis=1).astype(np.int16)
        sd.play(data, rate, device=device, blocking=False)
    except Exception as e:
        logging.warning("Could not play %s: %s", path, e)
