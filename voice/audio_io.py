"""
Audio I/O Manager: Handles microphone capture and speaker playback with sounddevice.
Supports Push-to-Talk (PTT) key triggers and raw audio streaming buffers.
"""

import time
import numpy as np
try:
    import sounddevice as sd
except ImportError:
    sd = None
from typing import Optional, Callable
from core.config import settings
from core.logger import logger, log_latency

class AudioIO:
    def __init__(
        self,
        sample_rate: int = settings.voice.sample_rate,
        channels: int = settings.voice.channels,
        chunk_duration_ms: int = settings.voice.chunk_duration_ms
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = int(self.sample_rate * (chunk_duration_ms / 1000.0))
        self._is_recording = False
        self._recorded_chunks = []

    def record_chunked(self, duration_sec: float) -> np.ndarray:
        """
        Record audio for a fixed duration synchronously.
        Returns float32 normalized 1D numpy array.
        """
        if sd is None:
            logger.warning("sounddevice is not installed. Returning silent buffer.")
            return np.zeros(int(duration_sec * self.sample_rate), dtype=np.float32)

        with log_latency("AudioIO.record_chunked", f"{duration_sec}s"):
            audio = sd.rec(
                int(duration_sec * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32"
            )
            sd.wait()
            return audio.flatten()

    def play_audio(self, audio_data: np.ndarray, sample_rate: Optional[int] = None) -> None:
        """
        Play audio data array through system speakers synchronously.
        """
        if sd is None:
            logger.warning("sounddevice is not installed. Skipping audio playback.")
            return

        sr = sample_rate or self.sample_rate
        with log_latency("AudioIO.play_audio", f"{len(audio_data)/sr:.2f}s"):
            sd.play(audio_data, samplerate=sr)
            sd.wait()

    def start_recording(self) -> None:
        """Start buffering chunks for push-to-talk."""
        self._recorded_chunks = []
        self._is_recording = True

    def stop_recording(self) -> np.ndarray:
        """Stop buffering and return concatenated audio array."""
        self._is_recording = False
        if not self._recorded_chunks:
            return np.array([], dtype=np.float32)
        return np.concatenate(self._recorded_chunks, axis=0)

    def record_push_to_talk(self, is_pressed_fn: Callable[[], bool], poll_interval: float = 0.05) -> np.ndarray:
        """
        Records while is_pressed_fn returns True.
        """
        chunks = []
        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype="float32") as stream:
            while is_pressed_fn():
                data, _ = stream.read(self.chunk_size)
                chunks.append(data.flatten())
                time.sleep(poll_interval)
                
        if not chunks:
            return np.array([], dtype=np.float32)
        return np.concatenate(chunks, axis=0)
