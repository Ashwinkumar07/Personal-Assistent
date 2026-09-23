import unittest
import tempfile
from pathlib import Path

from adapters.network_router import NetworkRouter, NetworkMode
from core.device_axis import DeviceAxisManager, DeviceType
from memory.database import MemoryDatabase
from memory.manager import MemoryManager

class TestNetworkRouterAndAxis(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox = Path(self.temp_dir.name)
        self.db = MemoryDatabase(db_path=self.sandbox / "test_sync_mem.sqlite3")
        self.memory = MemoryManager(db=self.db)
        self.router = NetworkRouter(memory_manager=self.memory)
        self.axis_mgr = DeviceAxisManager()

    def tearDown(self):
        import gc
        del self.router
        del self.memory
        del self.db
        gc.collect()
        self.temp_dir.cleanup()

    def test_network_mode_detection(self):
        mode = self.router.detect_network_mode()
        self.assertIn(mode, [NetworkMode.HOME_LAN, NetworkMode.P2P_MESH, NetworkMode.OFFLINE_STANDALONE])

    def test_offline_delta_queue_and_flush(self):
        # 1. Queue offline updates
        self.router.queue_offline_update("fact", {"key": "coffee_pref", "value": "Espresso"})
        self.router.queue_offline_update("dialogue", {"role": "user", "content": "Offline voice command"})
        self.assertEqual(len(self.router.offline_queue), 2)

        # 2. Flush / Merge sync
        synced = self.router.flush_offline_delta_sync()
        self.assertEqual(synced, 2)
        self.assertEqual(len(self.router.offline_queue), 0)

        # 3. Verify merged into SQLite memory
        self.assertEqual(self.memory.get_fact("coffee_pref"), "Espresso")

    def test_device_axis_switching_and_routing(self):
        # 1. Default axis is Laptop
        self.assertEqual(self.axis_mgr.active_axis, DeviceType.LAPTOP)

        # 2. Switch to Phone axis
        self.axis_mgr.set_active_axis(DeviceType.PHONE, source_name="wireless_phone_mic")
        self.assertEqual(self.axis_mgr.active_axis, DeviceType.PHONE)

        # 3. Cross-dispatch rule test: PC task triggered on Phone routes execution target to Laptop
        route = self.axis_mgr.route_action("create_word_document", {"file_path": "report.docx"})
        self.assertEqual(route["origin_axis"], "PHONE")
        self.assertEqual(route["execution_target"], "LAPTOP")

if __name__ == "__main__":
    unittest.main()
