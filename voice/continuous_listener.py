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
    """Listens continuously for hands-free voice commands with adaptive noise calibration."""

    def __init__(
        self,
        on_command_callback: Optional[Callable[[str], str]] = None,
        tts_engine: Optional[TextToSpeech] = None
    ):
        self.sample_rate = 16000
        self.chunk_duration_sec = 0.2  # 200ms chunks for rapid responsiveness
        self.chunk_samples = int(self.sample_rate * self.chunk_duration_sec)
        
        self.vad = VoiceActivityDetector(sample_rate=self.sample_rate)
        self.stt: Optional[SpeechToText] = None
        self.tts = tts_engine or TextToSpeech()
        self.on_command_callback = on_command_callback
        
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._is_speaking = False
        self.ambient_rms = 0.015  # Default baseline noise floor

    def _init_stt(self) -> None:
        """Lazy load STT in background to avoid blocking startup."""
        if self.stt is None:
            try:
                self.stt = SpeechToText()
            except Exception as e:
                logger.error(f"[VOICE] STT initialization error: {e}")

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
        """Speak out loud while temporarily pausing microphone capture."""
        self._is_speaking = True
        try:
            self.tts.speak(text)
        finally:
            time.sleep(0.4)  # Echo cancellation grace period
            self._is_speaking = False

    def _calibrate_ambient(self, stream, num_chunks: int = 3) -> None:
        """Measure ambient room noise to establish dynamic energy threshold."""
        try:
            rms_vals = []
            for _ in range(num_chunks):
                chunk, _ = stream.read(self.chunk_samples)
                chunk_flat = chunk.flatten()
                val = float(np.sqrt(np.mean(chunk_flat**2)))
                rms_vals.append(val)
            if rms_vals:
                self.ambient_rms = float(np.mean(rms_vals))
                logger.info(f"[VOICE] Calibrated ambient noise floor: {self.ambient_rms:.4f}")
        except Exception as e:
            logger.debug(f"[VOICE] Noise calibration note: {e}")

    def _listen_loop(self) -> None:
        """Continuous audio chunk stream evaluator with adaptive threshold."""
        self._init_stt()
        
        try:
            import sounddevice as sd
        except ImportError:
            logger.warning("[VOICE] sounddevice is not installed. Voice listener disabled.")
            return

        speech_buffer = []
        silence_chunks = 0
        in_speech = False
        max_speech_chunks = 35  # ~7 seconds maximum utterance limit

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='float32') as stream:
                self._calibrate_ambient(stream)
                
                while self.is_running:
                    if self._is_speaking:
                        time.sleep(0.1)
                        # Reset buffer while assistant is speaking so it doesn't hear itself
                        speech_buffer = []
                        in_speech = False
                        silence_chunks = 0
                        continue

                    try:
                        audio_chunk, overflowed = stream.read(self.chunk_samples)
                    except Exception as e:
                        time.sleep(0.1)
                        continue

                    chunk_flat = audio_chunk.flatten()
                    chunk_rms = float(np.sqrt(np.mean(chunk_flat**2)))

                    # Dynamic speech threshold based on room background noise
                    speech_threshold = max(0.012, self.ambient_rms * 1.65)

                    if chunk_rms > speech_threshold:
                        speech_buffer.append(chunk_flat)
                        silence_chunks = 0
                        in_speech = True
                    elif in_speech:
                        silence_chunks += 1
                        speech_buffer.append(chunk_flat)

                        # End of utterance: ~0.8s silence (4 chunks) or hit max duration
                        if silence_chunks >= 4 or len(speech_buffer) >= max_speech_chunks:
                            full_audio = np.concatenate(speech_buffer)
                            speech_buffer = []
                            in_speech = False
                            silence_chunks = 0

                            # Process speech if length > 0.4 seconds
                            if len(full_audio) > int(self.sample_rate * 0.4) and self.stt:
                                try:
                                    # Trim silence from ends
                                    trimmed = self.vad.trim_silence(full_audio, threshold=self.ambient_rms * 1.1)
                                    target_audio = trimmed if len(trimmed) > int(self.sample_rate * 0.3) else full_audio
                                    
                                    text = self.stt.transcribe(target_audio)
                                    if text and len(text.strip()) > 1:
                                        print(f"\n[🎙️ Voice Input] Aswin: \"{text}\"")
                                        logger.info(f"[VOICE DETECTED] Aswin said: '{text}'")
                                        if self.on_command_callback:
                                            reply = self.on_command_callback(text)
                                            if reply:
                                                print(f"[🤖 Voice Output] Assistant: \"{reply}\"\n")
                                                self.speak(reply)
                                except Exception as e:
                                    logger.error(f"[VOICE] Transcription error: {e}")
                    else:
                        # Adapt ambient background noise tracking when quiet
                        self.ambient_rms = self.ambient_rms * 0.95 + chunk_rms * 0.05
        except Exception as e:
            logger.error(f"[VOICE] Microphone stream error: {e}")
