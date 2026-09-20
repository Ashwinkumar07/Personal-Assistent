import unittest
import tempfile
import json
from pathlib import Path
from core.safety_gate import SafetyGate, RiskLevel, SafetyViolationError

class TestSafetyGate(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox_path = Path(self.temp_dir.name)
        self.backup_dir = self.sandbox_path / "backups"
        self.audit_log = self.sandbox_path / "actions.jsonl"
        self.gate = SafetyGate(
            backup_dir=self.backup_dir,
            sandbox_dirs=[str(self.sandbox_path)],
            audit_log_path=self.audit_log
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_forbidden_action_blocked(self):
        with self.assertRaises(SafetyViolationError):
            self.gate.evaluate_and_authorize(
                tool_name="raw_shell_exec",
                risk_level=RiskLevel.FORBIDDEN,
                arguments={"cmd": "whoami"}
            )

    def test_sandbox_enforcement(self):
        forbidden_path = Path("C:/Windows/System32/drivers/etc/hosts")
        with self.assertRaises(SafetyViolationError):
            self.gate.evaluate_and_authorize(
                tool_name="write_file",
                risk_level=RiskLevel.WRITE,
                arguments={"file_path": str(forbidden_path), "content": "test"}
            )

    def test_pre_write_backup_creation(self):
        test_file = self.sandbox_path / "important.txt"
        test_file.write_text("Original content", encoding="utf-8")

        # Authorize write
        self.gate.evaluate_and_authorize(
            tool_name="write_file",
            risk_level=RiskLevel.WRITE,
            arguments={"file_path": str(test_file), "content": "Modified content"}
        )

        backups = list(self.backup_dir.glob("important_*.txt"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "Original content")

    def test_audit_log_writing(self):
        self.gate.log_action(
            tool_name="get_current_time",
            risk_level=RiskLevel.READ,
            arguments={},
            result="03:00:00 PM",
            confirmed=True
        )
        self.assertTrue(self.audit_log.exists())
        with open(self.audit_log, "r", encoding="utf-8") as f:
            entry = json.loads(f.readline())
            self.assertEqual(entry["tool"], "get_current_time")
            self.assertEqual(entry["risk_level"], "READ")

if __name__ == "__main__":
    unittest.main()
