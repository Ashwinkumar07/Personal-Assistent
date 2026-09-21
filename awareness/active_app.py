"""
Active Application Tracker:
Non-intrusive activity observer tracking foreground application usage time,
window titles, and productivity patterns at low polling frequency.
Strict Privacy: Never logs keystrokes, passwords, or raw screen contents.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.config import PROJECT_ROOT
from core.logger import logger

class ActivityObserver:
    def __init__(self, poll_interval_sec: float = 5.0):
        self.poll_interval_sec = poll_interval_sec
        self.is_active = False
        self._thread: Optional[threading.Thread] = None
        self._app_timeline: List[Dict[str, Any]] = []
        self._current_app: Optional[str] = None
        self._current_app_start: float = 0.0

    def start(self) -> None:
        """Start tracking focused app usage in background thread."""
        self.is_active = True
        self._thread = threading.Thread(target=self._observe_loop, daemon=True, name="ActivityObserver")
        self._thread.start()
        logger.info("[AWARENESS] Activity Observer started (polling every 5s).")

    def stop(self) -> None:
        """Stop tracking activity."""
        self.is_active = False
        self._record_session()
        logger.info("[AWARENESS] Activity Observer stopped.")

    def _observe_loop(self) -> None:
        while self.is_active:
            try:
                from awareness.uia_scanner import UIAutomationScanner
                scanner = UIAutomationScanner()
                win_info = scanner.get_active_window_info()
                proc = win_info.get("process_name", "unknown")
                title = win_info.get("title", "Untitled")

                if proc != self._current_app:
                    self._record_session()
                    self._current_app = proc
                    self._current_app_title = title
                    self._current_app_start = time.time()

            except Exception as e:
                logger.debug(f"[AWARENESS] Observer loop error: {e}")

            time.sleep(self.poll_interval_sec)

    def _record_session(self) -> None:
        if self._current_app and self._current_app_start > 0:
            duration_sec = time.time() - self._current_app_start
            if duration_sec >= 1.0:
                self._app_timeline.append({
                    "process_name": self._current_app,
                    "title": getattr(self, "_current_app_title", ""),
                    "duration_sec": round(duration_sec, 2),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._current_app_start))
                })

    def get_summary(self) -> Dict[str, float]:
        """Return total usage seconds per process name."""
        self._record_session()
        summary = {}
        for entry in self._app_timeline:
            proc = entry["process_name"]
            summary[proc] = summary.get(proc, 0.0) + entry["duration_sec"]
        return {k: round(v, 2) for k, v in summary.items()}
