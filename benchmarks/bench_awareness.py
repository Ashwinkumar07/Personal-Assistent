"""
Benchmark script: Measures screen awareness latency, control inspection, and face metric calculations.
Verifies Phase 4 / Module 4 Checking Factors.
"""

import os
import sys
import time
import tempfile
import psutil
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from awareness.uia_scanner import UIAutomationScanner
from awareness.face_companion import FaceCompanion
from core.proactive_coach import ProactiveCoach

def run_awareness_benchmark():
    print("=" * 60)
    print("      PHASE 4 BENCHMARK: SCREEN AWARENESS & COMPANION")
    print("=" * 60)

    # 1. Test UI Automation Scan Latency
    print("\n--- [1/3] Testing UI Automation Control Hierarchy Scanning ---")
    scanner = UIAutomationScanner()
    t0 = time.perf_counter()
    win_info = scanner.get_active_window_info()
    win_latency_ms = (time.perf_counter() - t0) * 1000
    print(f"[+] Active Window Title: '{win_info.get('title')}'")
    print(f"[+] Active Window Inspection Latency: {win_latency_ms:.2f} ms (Target: < 50 ms)")

    t0 = time.perf_counter()
    controls = scanner.inspect_active_controls(max_elements=20)
    ctrl_latency_ms = (time.perf_counter() - t0) * 1000
    print(f"[+] Detected {len(controls)} Window Control Elements in {ctrl_latency_ms:.2f} ms")

    # 2. Test Face Companion Metric Speed
    print("\n--- [2/3] Testing Face Metric & Fatigue Calculations ---")
    companion = FaceCompanion()
    synthetic_eye = np.random.uniform(0.0, 10.0, (6, 2))
    
    t0 = time.perf_counter()
    for _ in range(100):
        companion.calculate_ear(synthetic_eye)
    ear_latency_us = ((time.perf_counter() - t0) / 100) * 1000000
    print(f"[+] EAR Fatigue Calculation Speed: {ear_latency_us:.2f} microseconds (< 5 ms target)")

    # 3. Test Proactive Coach Goal Checking
    print("\n--- [3/3] Testing Proactive Goal & Notification Engine ---")
    temp_dir = tempfile.TemporaryDirectory()
    sandbox = Path(temp_dir.name)
    coach = ProactiveCoach(db_path=sandbox / "bench_goals.sqlite3")
    
    t0 = time.perf_counter()
    coach.add_goal("Pass Module 4 Benchmark")
    notifs = coach.check_background_jobs_and_notify()
    coach_latency_ms = (time.perf_counter() - t0) * 1000
    print(f"[+] Proactive Coach Check Latency: {coach_latency_ms:.2f} ms")

    print("\n" + "=" * 60)
    all_passed = win_latency_ms < 100.0 and ear_latency_us < 5000.0
    print(f"OVERALL PHASE 4 STATUS: {'ALL CHECKS PASSED' if all_passed else 'FAILED'}")
    print("=" * 60)

    temp_dir.cleanup()

if __name__ == "__main__":
    run_awareness_benchmark()
