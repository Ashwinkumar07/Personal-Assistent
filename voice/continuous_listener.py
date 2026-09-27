"""
==============================================================================
Hands-Free Continuous Voice Listener
==============================================================================
Runs in the background, continuously listening for speech via VAD.
When Aswin speaks, it captures audio, transcribes it with Whisper,
and dispatches it to the assistant loop with spoken TTS reply.
100% Offline, Local-Only processing.
==============================================================================
"""

import time
import threading
import queue
from typing import Callable, Optional
import numpy as np

from core.logger import logger
from core.config import settings
from voice.audio_io import AudioIO
from voice.vad import VoiceActivityDetector
from voice.stt import SpeechToText
from voice.tts import TextToSpeech

class ContinuousVoiceListener:
    """Listens continuously for hands-free voice commands."""

    def __init__(
        self,
        on_command_callback: Optional[Callable[[str], str]] = None,
        tts_engine: Optional[TextToSpeech] = None
    ):
        self.audio_io = AudioIO(sample_rate=16000)
        self.vad = VoiceActivityDetector()
        self.stt = None
        self.tts = tts_engine or TextToSpeech()
        self.on_command_callback = on_command_callback
        
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._is_speaking = False

    def _init_stt(self) -> None:
        """Lazy load STT to avoid blocking startup."""
        if self.stt is None:
            try:
                self.stt = SpeechToText()
            except Exception as e:
                logger.error(f"[VOICE] STT initialization note: {e}")

    def start(self) -> None:
        """Start continuous background listening."""
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("[VOICE] Continuous Hands-Free Voice Listener started.")

    def stop(self) -> None:
        """Stop listening."""
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("[VOICE] Continuous Voice Listener stopped.")

    def speak(self, text: str) -> None:
        """Speak out loud to Aswin while temporarily pausing mic echo."""
        self._is_speaking = True
        try:
            self.tts.speak(text)
        finally:
            time.sleep(0.3)  # Buffer to avoid hearing own echo
            self._is_speaking = False

    def _listen_loop(self) -> None:
        """Continuous audio chunk stream evaluator."""
        self._init_stt()
        sample_rate = 16000
        chunk_duration_sec = 0.5
        chunk_samples = int(sample_rate * chunk_duration_sec)
        
        speech_buffer = []
        silence_chunks = 0
        in_speech = False
        
        # Audio input stream
        try:
            import sounddevice as sd
            with sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32') as stream:
                while self.is_running:
                    if self._is_speaking:
                        time.sleep(0.1)
                        continue

                    audio_chunk, _ = stream.read(chunk_samples)
                    chunk_flat = audio_chunk.flatten()

                    has_speech = self.vad.is_speech_energy(chunk_flat, energy_threshold=0.018)

                    if has_speech:
                        speech_buffer.append(chunk_flat)
                        silence_chunks = 0
                        in_speech = True
                    elif in_speech:
                        silence_chunks += 1
                        speech_buffer.append(chunk_flat)

                        # End of utterance detected (~1.5s of silence after speech)
                        if silence_chunks >= 3:
                            full_audio = np.concatenate(speech_buffer)
                            speech_buffer = []
                            in_speech = False
                            silence_chunks = 0

                            # Transcribe if audio is meaningful length (>0.6s)
                            if len(full_audio) > int(sample_rate * 0.6) and self.stt:
                                try:
                                    text = self.stt.transcribe(full_audio)
                                    if text and len(text.strip()) > 1:
                                        logger.info(f"[VOICE DETECTED] Aswin said: '{text}'")
                                        if self.on_command_callback:
                                            reply = self.on_command_callback(text)
                                            if reply:
                                                self.speak(reply)
                                except Exception as e:
                                    logger.error(f"[VOICE] Transcription error: {e}")
                    else:
                        time.sleep(0.05)
        except Exception as e:
            logger.debug(f"[VOICE] Microphone stream note: {e}")
