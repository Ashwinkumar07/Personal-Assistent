"""
Background Worker Pool:
Executes asynchronous jobs from JobQueue at low CPU priority (BELOW_NORMAL_PRIORITY_CLASS)
so the system and foreground voice interaction never freeze or drop audio frames.
"""

import time
import threading
import psutil
from typing import Optional, List

from core.config import settings
from core.logger import logger, log_latency
from core.job_queue import JobQueue, JobStatus
from core.kill_switch import KillSwitch
from tools.registry import ToolRegistry

def set_low_cpu_priority() -> None:
    """Set the current worker thread/process to BELOW_NORMAL_PRIORITY_CLASS on Windows."""
    try:
        p = psutil.Process()
        if hasattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS"):
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            logger.debug("[WORKER] Process priority set to BELOW_NORMAL_PRIORITY_CLASS.")
    except Exception as e:
        logger.warning(f"[WORKER] Failed to set low CPU priority: {e}")

class WorkerPool:
    def __init__(
        self,
        queue: Optional[JobQueue] = None,
        registry: Optional[ToolRegistry] = None,
        kill_switch: Optional[KillSwitch] = None,
        max_workers: int = settings.concurrency.max_workers
    ):
        self.queue = queue or JobQueue()
        self.registry = registry or ToolRegistry()
        self.kill_switch = kill_switch or KillSwitch()
        self.max_workers = max_workers
        self._threads: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self.kill_switch.register_callback(self.stop)

    def _worker_loop(self, worker_id: int) -> None:
        """Worker thread execution loop."""
        set_low_cpu_priority()
        logger.info(f"[WORKER #{worker_id}] Background worker online and waiting for jobs.")

        while not self._stop_event.is_set() and not self.kill_switch.is_triggered:
            try:
                job = self.queue.fetch_next_job()
                if not job:
                    time.sleep(0.5)
                    continue

                job_id = job["id"]
                tool_name = job["tool_name"]
                args = job["arguments"]
                logger.info(f"[WORKER #{worker_id}] Processing Job #{job_id}: '{job['name']}' -> Tool: {tool_name}")

                # Execute through registry
                with log_latency(f"WorkerJob#{job_id}", tool_name):
                    res = self.registry.execute(tool_name, args)

                if res["success"]:
                    self.queue.complete_job(job_id, res["result"])
                else:
                    self.queue.fail_job(job_id, res["error"] or "Unknown execution failure")

            except Exception as e:
                logger.error(f"[WORKER #{worker_id}] Uncaught error in worker loop: {e}")
                time.sleep(1.0)

        logger.info(f"[WORKER #{worker_id}] Background worker stopped.")

    def start(self) -> None:
        """Start background worker threads."""
        self._stop_event.clear()
        self._threads = []
        for i in range(self.max_workers):
            t = threading.Thread(target=self._worker_loop, args=(i + 1,), daemon=True, name=f"AssistantWorker-{i+1}")
            t.start()
            self._threads.append(t)
        logger.info(f"[WORKER POOL] Started {self.max_workers} background workers.")

    def stop(self) -> None:
        """Signal all workers to stop immediately."""
        self._stop_event.set()
        logger.info("[WORKER POOL] Stop signal broadcast to all background workers.")
