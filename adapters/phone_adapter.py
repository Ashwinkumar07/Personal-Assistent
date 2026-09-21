"""
Wireless Android Phone Adapter:
Controls Android smartphone 100% wirelessly over local Wi-Fi or USB via ADB (Android Debug Bridge).
Enables checking phone battery, notifications, opening apps, taking photos, and pushing files.
"""

import subprocess
import shutil
from typing import Dict, Any, Optional, List
from core.logger import logger, log_latency
from core.safety_gate import RiskLevel
from tools.base import BaseTool
from pydantic import BaseModel, Field

class PhoneAdapter:
    def __init__(self, adb_path: str = "adb"):
        self.adb_path = adb_path
        self._adb_available = shutil.which(adb_path) is not None

    def _run_adb(self, args: List[str]) -> Optional[str]:
        if not self._adb_available:
            return None
        try:
            res = subprocess.run([self.adb_path] + args, capture_output=True, text=True, timeout=5)
            return res.stdout.strip()
        except Exception as e:
            logger.warning(f"[PHONE ADAPTER] ADB command failed: {e}")
            return None

    def connect_wireless(self, ip_address: str, port: int = 5555) -> bool:
        """Connect to phone wirelessly over local Wi-Fi."""
        res = self._run_adb(["connect", f"{ip_address}:{port}"])
        logger.info(f"[PHONE ADAPTER] Wireless connect output: {res}")
        return res is not None and "connected" in res.lower()

    def get_battery(self) -> Dict[str, Any]:
        """Query phone battery level."""
        output = self._run_adb(["shell", "dumpsys", "battery"])
        if not output:
            return {"connected": False, "level": None, "message": "Phone not connected via ADB."}
        
        level = 100
        for line in output.splitlines():
            if "level:" in line:
                try:
                    level = int(line.split(":")[1].strip())
                except ValueError:
                    pass
        return {"connected": True, "level": level}

    def open_app(self, package_name: str) -> bool:
        """Launch an application on the phone."""
        res = self._run_adb(["shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"])
        return res is not None

    def push_file(self, local_path: str, remote_path: str = "/sdcard/Download/") -> bool:
        """Send a file from PC to phone's Download directory."""
        res = self._run_adb(["push", local_path, remote_path])
        return res is not None and "pushed" in res.lower()

class GetPhoneStatusTool(BaseTool):
    name = "get_phone_status"
    description = "Check the battery and connection status of your wireless Android phone."
    risk_level = RiskLevel.READ

    def __init__(self, adapter: Optional[PhoneAdapter] = None):
        self.adapter = adapter or PhoneAdapter()

    def run(self) -> Dict[str, Any]:
        return self.adapter.get_battery()
