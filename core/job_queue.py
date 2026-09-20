"""
SQLite-Backed Asynchronous Job Queue:
Manages persistent background jobs with priorities, progress tracking, and cancellation.
"""

import sqlite3
import json
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.config import PROJECT_ROOT, settings
from core.logger import logger

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class JobPriority(int, Enum):
    HIGH = 1
    NORMAL = 5
    LOW = 10

class JobQueue:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (PROJECT_ROOT / settings.app.data_dir / "job_queue.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            # Enable WAL mode for high concurrency without locks
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    arguments_json TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    progress_message TEXT,
                    result_json TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def submit_job(
        self,
        name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL
    ) -> int:
        """Submit a new background job into the queue."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO jobs (name, tool_name, arguments_json, priority, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, tool_name, json.dumps(arguments), priority.value, JobStatus.QUEUED.value)
            )
            job_id = cursor.lastrowid
            conn.commit()
            logger.info(f"[JOB QUEUE] Job #{job_id} ('{name}') submitted [Priority: {priority.name}].")
            return job_id
        finally:
            conn.close()

    def fetch_next_job(self) -> Optional[Dict[str, Any]]:
        """Fetch the next highest priority queued job atomically."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, tool_name, arguments_json, priority, status
                FROM jobs
                WHERE status = ?
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
                """,
                (JobStatus.QUEUED.value,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            job_id, name, tool_name, args_json, priority, status = row
            cursor.execute(
                "UPDATE jobs SET status = ?, started_at = CURRENT_TIMESTAMP WHERE id = ?",
                (JobStatus.RUNNING.value, job_id)
            )
            conn.commit()
            return {
                "id": job_id,
                "name": name,
                "tool_name": tool_name,
                "arguments": json.loads(args_json),
                "priority": priority,
                "status": JobStatus.RUNNING.value,
            }
        finally:
            conn.close()

    def update_progress(self, job_id: int, progress: float, message: str = "") -> None:
        """Update job progress percentage (0.0 to 1.0) and status message."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "UPDATE jobs SET progress = ?, progress_message = ? WHERE id = ?",
                (progress, message, job_id)
            )
            conn.commit()
        finally:
            conn.close()

    def complete_job(self, job_id: int, result: Any) -> None:
        """Mark job as successfully completed with return results."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                UPDATE jobs 
                SET status = ?, progress = 1.0, result_json = ?, completed_at = CURRENT_TIMESTAMP 
                WHERE id = ?
                """,
                (JobStatus.COMPLETED.value, json.dumps(result, default=str), job_id)
            )
            conn.commit()
            logger.info(f"[JOB QUEUE] Job #{job_id} COMPLETED successfully.")
        finally:
            conn.close()

    def fail_job(self, job_id: int, error_message: str) -> None:
        """Mark job as failed with error details."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                UPDATE jobs 
                SET status = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP 
                WHERE id = ?
                """,
                (JobStatus.FAILED.value, error_message, job_id)
            )
            conn.commit()
            logger.error(f"[JOB QUEUE] Job #{job_id} FAILED: {error_message}")
        finally:
            conn.close()

    def cancel_job(self, job_id: int) -> bool:
        """Cancel a queued or running job."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE jobs SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ? AND status IN (?, ?)",
                (JobStatus.CANCELLED.value, job_id, JobStatus.QUEUED.value, JobStatus.RUNNING.value)
            )
            conn.commit()
            cancelled = cursor.rowcount > 0
            if cancelled:
                logger.info(f"[JOB QUEUE] Job #{job_id} CANCELLED by user request.")
            return cancelled
        finally:
            conn.close()

    def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve current status and details for a job ID."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, tool_name, arguments_json, priority, status, progress, progress_message, result_json, error_message, created_at, started_at, completed_at
                FROM jobs WHERE id = ?
                """,
                (job_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "tool_name": row[2],
                "arguments": json.loads(row[3]),
                "priority": row[4],
                "status": row[5],
                "progress": row[6],
                "progress_message": row[7],
                "result": json.loads(row[8]) if row[8] else None,
                "error": row[9],
                "created_at": row[10],
                "started_at": row[11],
                "completed_at": row[12],
            }
        finally:
            conn.close()

    def list_active_jobs(self) -> List[Dict[str, Any]]:
        """List all currently queued or running jobs."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, tool_name, priority, status, progress, progress_message
                FROM jobs WHERE status IN (?, ?)
                ORDER BY priority ASC, created_at ASC
                """,
                (JobStatus.QUEUED.value, JobStatus.RUNNING.value)
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "tool_name": r[2],
                    "priority": r[3],
                    "status": r[4],
                    "progress": r[5],
                    "progress_message": r[6]
                }
                for r in rows
            ]
        finally:
            conn.close()
