"""
Speech-to-Text (STT) Engine using faster-whisper (int8 quantized on CPU).
Optimized for Intel Core i7-10610U multi-threaded execution.
"""

import os
from pathlib import Path
from typing import Tuple, List, Optional
import numpy as np

from core.config import PROJECT_ROOT, settings
from core.logger import logger, log_latency

class SpeechToText:
    def __init__(
        self,
        model_size: str = settings.voice.stt.model_size,
        device: str = settings.voice.stt.device,
        compute_type: str = settings.voice.stt.compute_type,
        num_threads: int = settings.hardware.cpu_threads_stt,
        download_root: Optional[str] = None
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.num_threads = num_threads
        self.download_root = str(PROJECT_ROOT / (download_root or settings.voice.stt.download_root))
        
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load or initialize faster-whisper WhisperModel."""
        try:
            from faster_whisper import WhisperModel
            os.environ["OMP_NUM_THREADS"] = str(self.num_threads)
            logger.info(f"Loading STT model '{self.model_size}' (device={self.device}, compute={self.compute_type}, threads={self.num_threads})...")
            
            with log_latency("STT._load_model", self.model_size):
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    cpu_threads=self.num_threads,
                    download_root=self.download_root
                )
            logger.info("STT model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load faster-whisper model: {e}")
            self.model = None

    def transcribe(self, audio_data: np.ndarray, language: str = settings.voice.stt.language) -> str:
        """
        Transcribe audio numpy array (float32, 16kHz) to text.
        Returns cleaned string transcription.
        """
        if self.model is None:
            raise RuntimeError("STT model is not loaded. Please ensure faster-whisper is installed.")

        if len(audio_data) == 0:
            return ""

        with log_latency("STT.transcribe", f"{len(audio_data)/16000:.2f}s audio"):
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=settings.voice.stt.beam_size,
                language=language,
                vad_filter=True
            )
            transcription = " ".join([segment.text for segment in segments]).strip()
            return transcription
