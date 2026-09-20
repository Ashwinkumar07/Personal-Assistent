import unittest
import tempfile
from pathlib import Path
from core.orchestrator import Orchestrator
from core.safety_gate import SafetyGate
from core.kill_switch import KillSwitch
from tools.registry import ToolRegistry

class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox = Path(self.temp_dir.name)
        self.db_path = self.sandbox / "test_state.sqlite3"
        self.gate = SafetyGate(
            backup_dir=self.sandbox / "backups",
            sandbox_dirs=[str(self.sandbox)],
            audit_log_path=self.sandbox / "actions.jsonl"
        )
        self.kill_switch = KillSwitch()
        self.kill_switch.reset()
        self.orchestrator = Orchestrator(
            db_path=self.db_path,
            safety_gate=self.gate,
            kill_switch=self.kill_switch
        )

    def tearDown(self):
        self.kill_switch.reset()
        del self.orchestrator
        import gc
        gc.collect()
        self.temp_dir.cleanup()

    def test_multi_step_plan_execution(self):
        test_file = self.sandbox / "plan_test.txt"
        steps = [
            {
                "tool": "write_text_file",
                "args": {"file_path": str(test_file), "content": "Step 1 text."},
                "description": "Write initial file"
            },
            {
                "tool": "read_text_file",
                "args": {"file_path": str(test_file)},
                "description": "Read file back"
            },
            {
                "tool": "get_current_time",
                "args": {},
                "description": "Check current time"
            }
        ]

        result = self.orchestrator.execute_plan("Test Multi-Step Execution", steps)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["step_results"]), 3)
        self.assertEqual(result["step_results"][1]["result"], "Step 1 text.")

    def test_kill_switch_aborts_execution(self):
        # Trigger kill switch before plan execution
        self.kill_switch.trigger(source="UNIT_TEST")
        
        steps = [
            {"tool": "get_current_time", "args": {}, "description": "Check time"}
        ]
        result = self.orchestrator.execute_plan("Aborted Plan", steps)
        self.assertFalse(result["success"])
        self.assertIn("Kill Switch", result["error"])

if __name__ == "__main__":
    unittest.main()
