import unittest
import tempfile
import numpy as np
from pathlib import Path

from awareness.uia_scanner import UIAutomationScanner
from awareness.ocr_scanner import ScreenOCRScanner
from awareness.active_app import ActivityObserver
from awareness.face_companion import FaceCompanion
from core.proactive_coach import ProactiveCoach
from core.job_queue import JobQueue

class TestAwarenessAndCoach(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox = Path(self.temp_dir.name)

    def tearDown(self):
        import gc
        gc.collect()
        self.temp_dir.cleanup()

    def test_uia_active_window(self):
        scanner = UIAutomationScanner()
        win = scanner.get_active_window_info()
        self.assertIn("title", win)
        self.assertIn("hwnd", win)

    def test_face_companion_ear_calculation(self):
        companion = FaceCompanion()
        # Synthetic open eye points
        open_eye = np.array([
            [0.0, 0.0], [1.0, 1.0], [2.0, 1.0],
            [3.0, 0.0], [2.0, -1.0], [1.0, -1.0]
        ])
        ear_open = companion.calculate_ear(open_eye)
        self.assertGreater(ear_open, 0.2)

        # Synthetic closed eye points (vertical distances near 0)
        closed_eye = np.array([
            [0.0, 0.0], [1.0, 0.05], [2.0, 0.05],
            [3.0, 0.0], [2.0, -0.05], [1.0, -0.05]
        ])
        ear_closed = companion.calculate_ear(closed_eye)
        self.assertLess(ear_closed, 0.1)

    def test_proactive_coach_goal_lifecycle(self):
        db_path = self.sandbox / "test_goals.sqlite3"
        job_db = self.sandbox / "test_jobs.sqlite3"
        queue = JobQueue(db_path=job_db)
        coach = ProactiveCoach(db_path=db_path, job_queue=queue)

        # 1. Add goal
        gid = coach.add_goal("Complete Module 4")
        self.assertIsInstance(gid, int)

        # 2. List active goals
        active = coach.list_active_goals()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["title"], "Complete Module 4")

        # 3. Complete goal
        completed = coach.complete_goal(gid)
        self.assertTrue(completed)
        self.assertEqual(len(coach.list_active_goals()), 0)

    def test_activity_observer_summary(self):
        observer = ActivityObserver(poll_interval_sec=0.1)
        observer.start()
        import time
        time.sleep(0.3)
        observer.stop()
        summary = observer.get_summary()
        self.assertIsInstance(summary, dict)

if __name__ == "__main__":
    unittest.main()
