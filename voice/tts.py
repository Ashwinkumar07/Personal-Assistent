"""
Text-to-Speech (TTS) Engine supporting sentence-by-sentence streaming.
Supports Piper TTS / Windows SAPI fallback to ensure ultra-low first-sentence latency (<800ms).
"""

import re
import queue
import threading
from pathlib import Path
from typing import Generator, Optional, List
import numpy as np

from core.config import PROJECT_ROOT, settings
from core.logger import logger, log_latency
from voice.audio_io import AudioIO

class TextToSpeech:
    def __init__(
        self,
        model_name: str = settings.voice.tts.model_name,
        models_dir: Optional[str] = None,
        sample_rate: int = settings.voice.tts.sample_rate
    ):
        self.model_name = model_name
        self.models_dir = Path(PROJECT_ROOT / (models_dir or settings.voice.tts.models_dir))
        self.sample_rate = sample_rate
        self.audio_io = AudioIO(sample_rate=sample_rate)
        self._piper_voice = None
        self._sapi_engine = None
        self._init_engine()

    def _init_engine(self) -> None:
        """Initialize Piper TTS or fallback to Windows COM SAPI."""
        try:
            # Check for piper-tts
            from piper import PiperVoice
            model_path = self.models_dir / f"{self.model_name}.onnx"
            config_path = self.models_dir / f"{self.model_name}.onnx.json"
            
            if model_path.exists() and config_path.exists():
                logger.info(f"Loading Piper voice from {model_path}...")
                with log_latency("TTS._init_piper", self.model_name):
                    self._piper_voice = PiperVoice.load(str(model_path), config_path=str(config_path))
                return
        except Exception as e:
            logger.debug(f"Piper voice init skipped/failed: {e}")

        # Fallback to pyttsx3 (SAPI5 on Windows - zero external download needed)
        try:
            import pyttsx3
            logger.info("Initializing Windows SAPI TTS fallback engine...")
            self._sapi_engine = pyttsx3.init()
            self._sapi_engine.setProperty('rate', 190)
        except Exception as e:
            logger.warning(f"Could not initialize SAPI TTS: {e}")

    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences for low-latency streaming playback."""
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def speak(self, text: str) -> None:
        """
        Synthesize and speak complete text by streaming sentence by sentence.
        """
        if not text.strip():
            return

        sentences = self.split_sentences(text)
        for sentence in sentences:
            with log_latency("TTS.speak_sentence", sentence[:30]):
                if self._sapi_engine:
                    self._sapi_engine.say(sentence)
                    self._sapi_engine.runAndWait()
                elif self._piper_voice:
                    # Synthesize with Piper
                    import io
                    import wave
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, "wb") as wav_file:
                        self._piper_voice.synthesize(sentence, wav_file)
                    wav_io.seek(0)
                    with wave.open(wav_io, "rb") as wav_file:
                        frames = wav_file.readframes(wav_file.getnframes())
                        audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                        self.audio_io.play_audio(audio_data, sample_rate=self.sample_rate)
                else:
                    logger.warning(f"[TTS Fallback Console]: {sentence}")
