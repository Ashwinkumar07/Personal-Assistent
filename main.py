"""
Master Bootstrap & Entry Point:
Fully Local, Free, and Independent Desktop Assistant for Windows 11.
"""

import sys
import time
import signal
from pathlib import Path

# Add workspace to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import settings
from core.logger import logger
from core.safety_gate import SafetyGate
from core.kill_switch import KillSwitch
from core.job_queue import JobQueue
from core.worker import WorkerPool
from core.orchestrator import Orchestrator
from core.proactive_coach import ProactiveCoach
from tools.registry import ToolRegistry
from tools.builtins import register_default_tools
from adapters.browser_adapter import BrowserAdapter
from adapters.downloader import DownloaderAdapter
from adapters.phone_adapter import GetPhoneStatusTool
from adapters.office_adapter import CreateWordDocumentTool
from adapters.code_adapter import GitStatusTool, OpenVSCodeTool
from memory.manager import MemoryManager
from awareness.active_app import ActivityObserver
from brain.llm_client import PluggableLLMClient
from ui.tray_app import SystemTrayApp

def main():
    print("=" * 65)
    print(f"      {settings.app.name.upper()} v{settings.app.version}")
    print("      Fully Local, Autonomous, Resource-Optimized Windows 11")
    print("=" * 65)

    # 1. Initialize Safety & Core Infrastructure
    kill_switch = KillSwitch()
    safety_gate = SafetyGate()
    registry = ToolRegistry(safety_gate=safety_gate)

    # 2. Register Builtin Tools & App Adapters
    register_default_tools(registry)
    registry.register(BrowserAdapter())
    registry.register(DownloaderAdapter())
    registry.register(GetPhoneStatusTool())
    registry.register(CreateWordDocumentTool())
    registry.register(GitStatusTool())
    registry.register(OpenVSCodeTool())

    logger.info(f"Loaded {len(registry.list_tools())} total capabilities and tools.")

    # 3. Start Background Job Workers & Awareness Observers
    job_queue = JobQueue()
    worker_pool = WorkerPool(queue=job_queue, registry=registry, kill_switch=kill_switch)
    worker_pool.start()

    activity_observer = ActivityObserver(poll_interval_sec=10.0)
    activity_observer.start()

    memory_mgr = MemoryManager()
    coach = ProactiveCoach(job_queue=job_queue)
    orchestrator = Orchestrator(registry=registry, safety_gate=safety_gate, kill_switch=kill_switch)
    brain = PluggableLLMClient()

    # 4. Launch System Tray Icon
    tray_app = SystemTrayApp(kill_switch=kill_switch, on_exit_callback=worker_pool.stop)
    tray_app.run_in_background()

    print("\n[✔] Assistant is ONLINE and ready for commands.")
    print(f"[!] Global Kill Switch Hotkey: '{settings.safety.kill_switch_hotkey}'")
    print("[!] Type a command below or press Ctrl+C to exit.\n")

    def shutdown():
        print("\nShutting down assistant...")
        worker_pool.stop()
        activity_observer.stop()
        kill_switch.stop_listener()
        print("Goodbye!")
        sys.exit(0)

    # Command loop (Interactive CLI / Voice bridge)
    try:
        while not kill_switch.is_triggered:
            try:
                user_cmd = input("You > ").strip()
                if not user_cmd:
                    continue
                if user_cmd.lower() in ("exit", "quit"):
                    shutdown()

                # Brain decomposes command into steps
                steps = brain.plan_steps(user_cmd, registry.get_all_schemas())
                print(f"[Brain Plan] {len(steps)} step(s): {steps}")

                # Orchestrator executes steps under Safety Gate
                result = orchestrator.execute_plan(user_cmd, steps)
                print(f"[Assistant] Result: {result.get('step_results')}\n")

                # Check for completed background jobs
                coach.check_background_jobs_and_notify()

            except (KeyboardInterrupt, EOFError):
                shutdown()
    finally:
        shutdown()

if __name__ == "__main__":
    main()
