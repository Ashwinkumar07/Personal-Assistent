"""
Benchmark script: Measures Safety Gate latency, Kill Switch emergency halt time, and audit log integrity.
Verifies Phase 2 / Module 2 Checking Factors.
"""

import sys
import time
import tempfile
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.safety_gate import SafetyGate, RiskLevel
from core.kill_switch import KillSwitch
from tools.registry import ToolRegistry
from tools.builtins import register_default_tools

def run_safety_benchmark():
    print("=" * 60)
    print("      PHASE 2 BENCHMARK: SAFETY GATE & KILL SWITCH")
    print("=" * 60)

    temp_dir = tempfile.TemporaryDirectory()
    sandbox = Path(temp_dir.name)
    audit_file = sandbox / "actions.jsonl"
    
    gate = SafetyGate(
        backup_dir=sandbox / "backups",
        sandbox_dirs=[str(sandbox)],
        audit_log_path=audit_file
    )
    registry = ToolRegistry(safety_gate=gate)
    register_default_tools(registry)
    kill_switch = KillSwitch()

    # 1. Kill Switch Reaction Latency
    print("\n--- [1/3] Testing Emergency Kill Switch Latency ---")
    stop_called = False
    def mock_worker_stop():
        nonlocal stop_called
        stop_called = True

    kill_switch.register_callback(mock_worker_stop)
    t0 = time.perf_counter()
    latency_ms = kill_switch.trigger(source="BENCHMARK")
    print(f"[+] Kill Switch Halt Latency: {latency_ms:.2f} ms (Target: < 1000 ms)")
    ks_pass = latency_ms < 1000.0 and stop_called
    print(f"    Kill Switch Status: {'PASSED' if ks_pass else 'FAILED'}")
    kill_switch.reset()

    # 2. Safety Gate Evaluation Overhead
    print("\n--- [2/3] Testing Safety Gate Evaluation Latency ---")
    t0 = time.perf_counter()
    for _ in range(100):
        gate.evaluate_and_authorize("get_current_time", RiskLevel.READ, {})
    eval_latency_avg_ms = ((time.perf_counter() - t0) / 100) * 1000
    print(f"[+] Average Safety Gate Check Latency: {eval_latency_avg_ms:.3f} ms (Target: < 10 ms)")
    sg_pass = eval_latency_avg_ms < 10.0
    print(f"    Safety Evaluation Status: {'PASSED' if sg_pass else 'FAILED'}")

    # 3. Action Audit Log Integrity
    print("\n--- [3/3] Testing 100% Action Audit Logging ---")
    test_file = sandbox / "bench_log.txt"
    registry.execute("write_text_file", {"file_path": str(test_file), "content": "Sample"})
    registry.execute("read_text_file", {"file_path": str(test_file)})
    registry.execute("get_current_time", {})

    with open(audit_file, "r", encoding="utf-8") as f:
        log_lines = f.readlines()

    logged_count = len(log_lines)
    print(f"[+] Total Executed Actions: 3 | Total Audit Log Entries: {logged_count}")
    log_pass = logged_count == 3
    print(f"    Audit Integrity Status: {'PASSED' if log_pass else 'FAILED'}")

    print("\n" + "=" * 60)
    print(f"OVERALL PHASE 2 STATUS: {'ALL CHECKS PASSED' if (ks_pass and sg_pass and log_pass) else 'FAILED'}")
    print("=" * 60)
    temp_dir.cleanup()

if __name__ == "__main__":
    run_safety_benchmark()
