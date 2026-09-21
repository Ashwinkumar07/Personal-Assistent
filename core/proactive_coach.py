"""
Proactive Focus & Goal Coach:
Tracks active user goals, monitors background task updates, and periodically
provides casual, encouraging check-ins and break suggestions.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import sqlite3

from core.config import PROJECT_ROOT
from core.logger import logger
from core.job_queue import JobQueue, JobStatus
from awareness.face_companion import FaceCompanion

class ProactiveCoach:
    def __init__(
        self,
        db_path: Optional[Path] = None,
        job_queue: Optional[JobQueue] = None,
        face_companion: Optional[FaceCompanion] = None,
        notify_callback: Optional[Callable[[str], None]] = None
    ):
        self.db_path = db_path or (PROJECT_ROOT / "data" / "goals.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.job_queue = job_queue or JobQueue()
        self.face_companion = face_companion or FaceCompanion()
        self.notify_callback = notify_callback or (lambda msg: logger.info(f"[PROACTIVE COACH] {msg}"))
        
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._last_notified_job_ids = set()
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    target_time TIMESTAMP,
                    status TEXT DEFAULT 'IN_PROGRESS',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def add_goal(self, title: str) -> int:
        """Add a new focus goal to track."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO goals (title) VALUES (?)", (title,))
            goal_id = cursor.lastrowid
            conn.commit()
            logger.info(f"[GOAL COACH] Goal #{goal_id} added: '{title}'")
            return goal_id
        finally:
            conn.close()

    def list_active_goals(self) -> List[Dict[str, Any]]:
        """List active in-progress goals."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, created_at FROM goals WHERE status = 'IN_PROGRESS'")
            rows = cursor.fetchall()
            return [{"id": r[0], "title": r[1], "created_at": r[2]} for r in rows]
        finally:
            conn.close()

    def complete_goal(self, goal_id: int) -> bool:
        """Mark a goal as accomplished."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE goals SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE id = ?", (goal_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def check_background_jobs_and_notify(self) -> List[str]:
        """Check for recently completed background jobs and trigger alerts."""
        notifications = []
        conn = sqlite3.connect(self.job_queue.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM jobs WHERE status = 'COMPLETED'")
            rows = cursor.fetchall()
            for jid, name in rows:
                if jid not in self._last_notified_job_ids:
                    self._last_notified_job_ids.add(jid)
                    msg = f"Hey! Background task '{name}' is completed."
                    notifications.append(msg)
                    self.notify_callback(msg)
        except Exception as e:
            logger.debug(f"[GOAL COACH] Job check error: {e}")
        finally:
            conn.close()
        return notifications
