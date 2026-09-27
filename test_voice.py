"""
==============================================================================
Voice Diagnostic & Live Calibration Tool
==============================================================================
Tests microphone input, ambient room noise calibration, offline Whisper STT,
and native Windows SAPI TTS spoken reply.
==============================================================================
"""

import sys
import time
import numpy as np
from pathlib import Path

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from voice.tts import TextToSpeech
from voice.stt import SpeechToText
from voice.vad import VoiceActivityDetector

def main():
    print("=" * 65)
    print("        PERSONAL ASSISTANT - VOICE SYSTEM TEST")
    print("=" * 65)

    # 1. Test TTS Output
    print("\n[1/3] Testing Audio Output (Speakers)...")
    tts = TextToSpeech()
    test_phrase = "Voice test initiated. Audio output is working properly."
    print(f"  🔊 Speaking: \"{test_phrase}\"")
    tts.speak(test_phrase)
    print("  ✔ Audio output test complete.")

    # 2. Test STT Initialization
    print("\n[2/3] Loading Offline Whisper Speech-to-Text Model...")
    stt = SpeechToText()
    if stt.model is None:
        print("  ❌ Faster-Whisper model could not be loaded.")
        return
    print("  ✔ Whisper STT engine ready.")

    # 3. Test Microphone Recording & Live STT
    print("\n[3/3] Testing Microphone Input (3 Seconds)...")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        print(f"  🎙️ Active Input Device: {sd.default.device}")
        
        print("\n  👉 Speak something into your microphone now (e.g., 'Hello Assistant')...")
        print("  [Recording in 3... 2... 1... GO!]")
        
        fs = 16000
        duration = 3.5  # seconds
        audio_rec = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
        
        for i in range(int(duration)):
            time.sleep(1)
            print(f"  ⏳ Listening... ({i+1}/{int(duration)}s)")
        sd.wait()

        audio_flat = audio_rec.flatten()
        rms = float(np.sqrt(np.mean(audio_flat**2)))
        peak = float(np.max(np.abs(audio_flat)))
        print(f"\n  📊 Audio Captured: RMS Energy = {rms:.5f}, Peak = {peak:.5f}")

        if rms < 0.003:
            print("  ⚠️ Warning: Recorded audio level is very low. Please check Windows microphone volume.")

        print("  🔄 Transcribing audio with local Whisper...")
        transcription = stt.transcribe(audio_flat)
        
        if transcription and len(transcription.strip()) > 0:
            print(f"\n  🎉 [SUCCESS] You said: \"{transcription}\"")
            reply = f"I heard you loud and clear! You said: {transcription}"
            print(f"  🔊 Assistant Reply: \"{reply}\"")
            tts.speak(reply)
        else:
            print("  ⚠️ No speech was recognized. Try speaking louder or closer to the microphone.")
            tts.speak("I could not detect clear speech. Please check your microphone volume.")

    except Exception as e:
        print(f"  ❌ Microphone error: {e}")

    print("\n" + "=" * 65)
    print("Voice test finished!")
    print("=" * 65)

if __name__ == "__main__":
    main()
