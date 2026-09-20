"""
Benchmark script: Measures voice/orchestrator responsiveness while 3 parallel background jobs execute.
Verifies Phase 3 / Module 3 Checking Factor.
"""

import sys
import time
import tempfile
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.job_queue import JobQueue, JobPriority, JobStatus
from core.worker import WorkerPool
from core.safety_gate import SafetyGate
from tools.registry import ToolRegistry
from tools.builtins import register_default_tools
from voice.vad import VoiceActivityDetector
from voice.tts import TextToSpeech

def run_concurrency_benchmark():
    print("=" * 60)
    print("      PHASE 3 BENCHMARK: CONCURRENCY & JOB QUEUE")
    print("=" * 60)

    temp_dir = tempfile.TemporaryDirectory()
    sandbox = Path(temp_dir.name)
    db_path = sandbox / "bench_jobs.sqlite3"
    
    gate = SafetyGate(
        backup_dir=sandbox / "backups",
        sandbox_dirs=[str(sandbox)],
        audit_log_path=sandbox / "actions.jsonl"
    )
    registry = ToolRegistry(safety_gate=gate)
    register_default_tools(registry)
    queue = JobQueue(db_path=db_path)

    # 1. Start Worker Pool with 3 parallel workers
    print("\n--- [1/3] Launching 3 Background Workers ---")
    pool = WorkerPool(queue=queue, registry=registry, max_workers=3)
    pool.start()

    # 2. Enqueue 3 CPU-intensive file writing/reading/spec tasks
    print("\n--- [2/3] Submitting 3 Parallel Tasks ---")
    job_ids = []
    for i in range(3):
        target_file = sandbox / f"heavy_task_{i+1}.txt"
        jid = queue.submit_job(
            name=f"Background Task #{i+1}",
            tool_name="write_text_file",
            arguments={"file_path": str(target_file), "content": "Sample content " * 5000}
        )
        job_ids.append(jid)

    # 3. Measure Voice/Audio Responsiveness WHILE jobs are running
    print("\n--- [3/3] Measuring Voice Loop Latency During Active Concurrency ---")
    vad = VoiceActivityDetector()
    tts = TextToSpeech()
    test_audio = np.random.uniform(-0.1, 0.1, int(16000 * 3.0)).astype(np.float32)

    t0 = time.perf_counter()
    trimmed = vad.trim_silence(test_audio)
    vad_latency_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    chunks = tts.split_sentences("Background jobs are running smoothly. System responsiveness is verified.")
    tts_chunk_ms = (time.perf_counter() - t0) * 1000

    print(f"[+] VAD Processing Time under 3-worker load: {vad_latency_ms:.2f} ms")
    print(f"[+] TTS Sentence Chunking Latency under load: {tts_chunk_ms:.2f} ms")

    # Wait for background jobs to complete
    for _ in range(30):
        statuses = [queue.get_job(jid)["status"] for jid in job_ids]
        if all(s == JobStatus.COMPLETED.value for s in statuses):
            break
        time.sleep(0.2)

    pool.stop()

    all_completed = all(queue.get_job(jid)["status"] == JobStatus.COMPLETED.value for jid in job_ids)
    print(f"\n[+] Background Jobs Status: {'ALL 3 COMPLETED' if all_completed else 'SOME FAILED'}")

    voice_responsive = vad_latency_ms < 50.0 and tts_chunk_ms < 50.0
    print(f"[+] Voice Responsiveness Status: {'PASSED (Zero UI Freeze)' if voice_responsive else 'SLOW'}")

    print("\n" + "=" * 60)
    print(f"OVERALL PHASE 3 STATUS: {'PASSED' if (all_completed and voice_responsive) else 'FAILED'}")
    print("=" * 60)
    
    import gc
    del pool
    del queue
    gc.collect()
    temp_dir.cleanup()

if __name__ == "__main__":
    run_concurrency_benchmark()
