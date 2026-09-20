import unittest
import tempfile
from pathlib import Path
from tools.registry import ToolRegistry
from tools.builtins import register_default_tools
from core.safety_gate import SafetyGate

class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox = Path(self.temp_dir.name)
        self.gate = SafetyGate(
            backup_dir=self.sandbox / "backups",
            sandbox_dirs=[str(self.sandbox)],
            audit_log_path=self.sandbox / "actions.jsonl"
        )
        self.registry = ToolRegistry(safety_gate=self.gate)
        register_default_tools(self.registry)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_registered_tools_count(self):
        tools = self.registry.list_tools()
        self.assertGreaterEqual(len(tools), 15)

    def test_get_current_time(self):
        res = self.registry.execute("get_current_time", {})
        self.assertTrue(res["success"])
        self.assertIsInstance(res["result"], str)

    def test_get_system_specs(self):
        res = self.registry.execute("get_system_specs", {})
        self.assertTrue(res["success"])
        self.assertIn("cpu_percent", res["result"])
        self.assertIn("ram_available_gb", res["result"])

    def test_file_write_and_read(self):
        test_file = self.sandbox / "note.txt"
        write_res = self.registry.execute("write_text_file", {
            "file_path": str(test_file),
            "content": "Automated test note content."
        })
        self.assertTrue(write_res["success"])

        read_res = self.registry.execute("read_text_file", {
            "file_path": str(test_file)
        })
        self.assertTrue(read_res["success"])
        self.assertEqual(read_res["result"], "Automated test note content.")

    def test_schema_export(self):
        schemas = self.registry.get_all_schemas()
        self.assertGreaterEqual(len(schemas), 15)
        self.assertTrue(all("function" in s for s in schemas))

if __name__ == "__main__":
    unittest.main()
