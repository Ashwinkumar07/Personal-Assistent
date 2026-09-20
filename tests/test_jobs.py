import unittest
import tempfile
import time
from pathlib import Path
from core.job_queue import JobQueue, JobPriority, JobStatus
from core.worker import WorkerPool
from core.safety_gate import SafetyGate
from tools.registry import ToolRegistry
from tools.builtins import register_default_tools

class TestJobQueueAndWorkers(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox = Path(self.temp_dir.name)
        self.db_path = self.sandbox / "test_jobs.sqlite3"
        self.queue = JobQueue(db_path=self.db_path)
        
        self.gate = SafetyGate(
            backup_dir=self.sandbox / "backups",
            sandbox_dirs=[str(self.sandbox)],
            audit_log_path=self.sandbox / "actions.jsonl"
        )
        self.registry = ToolRegistry(safety_gate=self.gate)
        register_default_tools(self.registry)

    def tearDown(self):
        import gc
        del self.queue
        del self.registry
        gc.collect()
        self.temp_dir.cleanup()

    def test_job_submission_and_priority(self):
        # Submit low priority job first, then high priority
        job1 = self.queue.submit_job("Low Task", "get_current_time", {}, priority=JobPriority.LOW)
        job2 = self.queue.submit_job("High Task", "get_current_date", {}, priority=JobPriority.HIGH)

        # First fetched job must be the HIGH priority job
        fetched = self.queue.fetch_next_job()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], job2)
        self.assertEqual(fetched["tool_name"], "get_current_date")

    def test_job_cancellation(self):
        job_id = self.queue.submit_job("Cancel Me", "get_current_time", {})
        cancelled = self.queue.cancel_job(job_id)
        self.assertTrue(cancelled)

        job_info = self.queue.get_job(job_id)
        self.assertEqual(job_info["status"], JobStatus.CANCELLED.value)

    def test_worker_pool_execution(self):
        test_file = self.sandbox / "worker_output.txt"
        job_id = self.queue.submit_job(
            "Worker File Task",
            "write_text_file",
            {"file_path": str(test_file), "content": "Written by background worker."}
        )

        pool = WorkerPool(queue=self.queue, registry=self.registry, max_workers=2)
        pool.start()

        # Wait for worker to pick up and finish job
        for _ in range(20):
            job_info = self.queue.get_job(job_id)
            if job_info["status"] == JobStatus.COMPLETED.value:
                break
            time.sleep(0.2)

        pool.stop()

        job_info = self.queue.get_job(job_id)
        self.assertEqual(job_info["status"], JobStatus.COMPLETED.value)
        self.assertTrue(test_file.exists())
        self.assertEqual(test_file.read_text(encoding="utf-8"), "Written by background worker.")

if __name__ == "__main__":
    unittest.main()
