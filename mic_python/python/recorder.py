import logging

import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import time
import os

class Recorder:
    def __init__(self, output_file=None, silence_threshold=2.0, silence_level=1000):
        """
        Initializes the Recorder.

        :param output_file: Path to save the recorded audio file. If None, a temp file will be used.
        :param silence_threshold: Duration of silence in seconds to stop recording automatically.
        :param silence_level: Audio level considered as silence (lower means more sensitive).
        """
        self.output_file = output_file or self._generate_temp_filename()
        self.silence_threshold = silence_threshold
        self.silence_level = silence_level
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

    def _generate_temp_filename(self):
        temp_dir = os.getenv('TEMP', '/tmp')
        timestamp = int(time.time())
        return os.path.join(temp_dir, f"recording_{timestamp}.ogg")

    def start_recording(self, silence_grace_period=0):
        """
        Starts recording audio from the microphone.

        :param silence_grace_period: Duration in seconds to ignore silence at the beginning of the recording.
        """
        with self._lock:
            if self._recording:
                logging.info("Already recording.")
                return
            self._recording = True
            self._audio_frames = []
            self._silence_start = None
            self._should_stop = False

            self._stream = sd.InputStream(samplerate=self._rate,
                                          channels=self._channels,
                                          dtype=self._dtype,
                                          callback=self._audio_callback)
            self._stream.start()
            logging.info("Recording started.")

        # Start a thread to monitor silence and stop recording
        threading.Thread(target=self._monitor_silence, args=(silence_grace_period,), daemon=True).start()

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
            logging.info("Recording stopped due to silence.")
            # print("Recording stopped and audio saved to:", self.output_file)

    def is_recording(self):
        """
        Returns True if currently recording, else False.
        """
        with self._lock:
            return self._recording

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback function for the InputStream.
        """
        if status:
            logging.debug("Stream status: %s", status)

        audio_data = indata.copy()
        self._audio_frames.append(audio_data)

        # Calculate audio level
        audio_level = np.abs(audio_data).mean()

        with self._lock:
            self._last_audio_level = audio_level

    def _monitor_silence(self, silence_grace_period=0):
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
                # Check if we are within the grace period
                if time.time() - start_time < silence_grace_period:
                    self._silence_start = None # Reset silence timer during grace period
                elif audio_level < self.silence_level:
                    if self._silence_start is None:
                        self._silence_start = time.time()
                    elif (time.time() - self._silence_start) >= self.silence_threshold:
                        self._should_stop = True
                else:
                    self._silence_start = None

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
        if self._stream:
            self._stream.stop()
            self._stream.close()
        sd.stop()
