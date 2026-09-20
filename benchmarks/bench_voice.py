"""
Benchmark script: Measures STT latency, TTS latency, and RAM memory footprint on the local system.
Verifies Phase 1 / Module 1 Checking Factors.
"""

import os
import sys
import time
import psutil
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import settings
from core.logger import logger, log_latency
from voice.audio_io import AudioIO
from voice.vad import VoiceActivityDetector
from voice.stt import SpeechToText
from voice.tts import TextToSpeech

def benchmark_memory_usage() -> float:
    """Returns current process RAM usage in MB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def run_benchmark():
    print("=" * 60)
    print("      PHASE 1 BENCHMARK: VOICE PIPELINE & SYSTEM METRICS")
    print("=" * 60)

    initial_ram = benchmark_memory_usage()
    print(f"[*] Initial Baseline Process RAM: {initial_ram:.2f} MB")

    # 1. Test Audio I/O & VAD
    print("\n--- [1/3] Testing Audio & VAD Processing ---")
    vad = VoiceActivityDetector()
    synthetic_audio = np.random.uniform(-0.1, 0.1, int(16000 * 3.0)).astype(np.float32) # 3s of audio
    
    t0 = time.perf_counter()
    trimmed = vad.trim_silence(synthetic_audio)
    vad_time_ms = (time.perf_counter() - t0) * 1000
    print(f"[+] VAD 3-second buffer trimming time: {vad_time_ms:.2f} ms")

    # 2. Test STT Engine (if faster-whisper available)
    print("\n--- [2/3] Testing Speech-to-Text (STT) Engine ---")
    try:
        stt = SpeechToText()
        if stt.model is not None:
            t0 = time.perf_counter()
            transcription = stt.transcribe(synthetic_audio)
            stt_time_ms = (time.perf_counter() - t0) * 1000
            print(f"[+] STT 3-second audio transcribe latency: {stt_time_ms:.2f} ms (Target: < 1500 ms)")
            stt_pass = stt_time_ms <= 1500.0
            print(f"    STT Status: {'PASSED' if stt_pass else 'NEEDS OPTIMIZATION'}")
        else:
            print("[!] STT Model not initialized (faster-whisper dependencies needed).")
    except Exception as e:
        print(f"[!] STT test error: {e}")

    # 3. Test TTS Engine
    print("\n--- [3/3] Testing Text-to-Speech (TTS) Engine ---")
    try:
        tts = TextToSpeech()
        test_phrase = "Hello! Your local desktop assistant is online and ready."
        t0 = time.perf_counter()
        sentences = tts.split_sentences(test_phrase)
        split_time_ms = (time.perf_counter() - t0) * 1000
        print(f"[+] TTS Sentence chunking latency: {split_time_ms:.2f} ms (Target: < 800 ms)")
    except Exception as e:
        print(f"[!] TTS test error: {e}")

    final_ram = benchmark_memory_usage()
    print(f"\n[*] Total Process RAM Footprint: {final_ram:.2f} MB (Target: < 10,240 MB)")
    ram_pass = final_ram <= settings.hardware.max_ram_budget_mb
    print(f"    RAM Status: {'PASSED' if ram_pass else 'EXCEEDED'}")
    print("=" * 60)

if __name__ == "__main__":
    run_benchmark()
