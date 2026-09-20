"""
Voice Activity Detection (VAD) module.
Provides energy-based fast thresholding and Silero VAD integration to detect speech segments.
"""

import numpy as np
from core.config import settings
from core.logger import logger

class VoiceActivityDetector:
    def __init__(
        self,
        threshold: float = settings.voice.vad.threshold,
        sample_rate: int = settings.voice.sample_rate
    ):
        self.threshold = threshold
        self.sample_rate = sample_rate

    def is_speech_energy(self, chunk: np.ndarray, energy_threshold: float = 0.015) -> bool:
        """
        Fast RMS-based energy calculation to filter silence without neural overhead.
        """
        if len(chunk) == 0:
            return False
        rms = np.sqrt(np.mean(chunk**2))
        return float(rms) > energy_threshold

    def trim_silence(self, audio: np.ndarray, frame_duration_ms: int = 30, threshold: float = 0.01) -> np.ndarray:
        """
        Trim leading and trailing silence from audio array using RMS framing.
        """
        if len(audio) == 0:
            return audio

        frame_len = int(self.sample_rate * (frame_duration_ms / 1000.0))
        num_frames = len(audio) // frame_len
        if num_frames == 0:
            return audio

        speech_indices = []
        for i in range(num_frames):
            frame = audio[i * frame_len : (i + 1) * frame_len]
            rms = np.sqrt(np.mean(frame**2))
            if rms > threshold:
                speech_indices.append(i)

        if not speech_indices:
            return np.array([], dtype=np.float32)

        start_idx = speech_indices[0] * frame_len
        end_idx = min(len(audio), (speech_indices[-1] + 1) * frame_len)
        return audio[start_idx:end_idx]
