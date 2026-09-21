import unittest
import tempfile
from pathlib import Path
from adapters.browser_adapter import BrowserAdapter
from adapters.downloader import DownloaderAdapter
from adapters.phone_adapter import PhoneAdapter
from memory.database import MemoryDatabase
from memory.manager import MemoryManager
from brain.llm_client import PluggableLLMClient

class TestAdaptersAndMemory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox = Path(self.temp_dir.name)
        self.db = MemoryDatabase(db_path=self.sandbox / "test_mem.sqlite3")
        self.memory = MemoryManager(db=self.db)

    def tearDown(self):
        import gc
        del self.memory
        del self.db
        gc.collect()
        self.temp_dir.cleanup()

    def test_semantic_memory_facts(self):
        self.memory.set_fact("user_name", "Ashwin", category="identity")
        self.assertEqual(self.memory.get_fact("user_name"), "Ashwin")

    def test_episodic_dialogue_history(self):
        self.memory.record_dialogue("user", "Hello assistant!")
        self.memory.record_dialogue("assistant", "Hello Ashwin, how can I help?")
        history = self.memory.get_recent_dialogue(limit=5)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["content"], "Hello assistant!")

    def test_procedural_workflow_saving(self):
        workflow_steps = [
            {"tool": "get_current_time", "args": {}},
            {"tool": "get_battery_status", "args": {}}
        ]
        self.memory.save_workflow("morning_routine", workflow_steps, "Daily morning check")
        saved = self.memory.get_workflow("morning_routine")
        self.assertEqual(len(saved), 2)

    def test_pluggable_brain_planning(self):
        brain = PluggableLLMClient()
        steps = brain.plan_steps("Check battery and system specs", [])
        self.assertGreaterEqual(len(steps), 1)
        self.assertEqual(steps[0]["tool"], "get_battery_status")

    def test_downloader_adapter(self):
        downloader = DownloaderAdapter(downloads_dir=self.sandbox)
        self.assertTrue(self.sandbox.exists())

if __name__ == "__main__":
    unittest.main()
