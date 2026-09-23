"""
Dynamic Multi-Device Active Axis Manager:
Designates whichever device hears your voice (Phone, Laptop, Desktop) as the
Primary Commander / Main Axis, while enabling seamless cross-device task dispatching.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from core.logger import logger, log_latency

class DeviceType(str, Enum):
    PHONE = "PHONE"
    LAPTOP = "LAPTOP"
    DESKTOP = "DESKTOP"

class DeviceAxisManager:
    def __init__(self, default_axis: DeviceType = DeviceType.LAPTOP):
        self.active_axis = default_axis
        self.connected_devices: Dict[str, Dict[str, Any]] = {
            "laptop": {"type": DeviceType.LAPTOP, "status": "ONLINE", "ip": "127.0.0.1"},
            "phone": {"type": DeviceType.PHONE, "status": "CONNECTED", "ip": "wireless_adb"}
        }

    def set_active_axis(self, device: DeviceType, source_name: str = "voice_origin") -> None:
        """Dynamically switch the main command axis to the device that captured the command."""
        previous = self.active_axis
        self.active_axis = device
        if previous != device:
            logger.info(f"[DEVICE AXIS] Main Axis switched from {previous.value} -> {device.value} (Origin: {source_name})")

    def route_action(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route tool execution based on the active axis:
        - If active axis is PHONE: Route media/apps to phone, cross-dispatch heavy tasks to PC.
        - If active axis is LAPTOP: Route desktop/office to PC, cross-dispatch mobile tasks to phone.
        """
        target_device = self.active_axis

        # Automatic cross-dispatch rules
        pc_tool_keywords = ["office", "word", "excel", "document", "vscode", "git", "download", "screen", "uia", "ocr"]
        phone_tool_keywords = ["phone", "sms", "mobile", "android", "call"]

        if self.active_axis == DeviceType.PHONE and any(k in tool_name.lower() for k in pc_tool_keywords):
            target_device = DeviceType.LAPTOP
            logger.info(f"[DEVICE AXIS] Cross-dispatching PC task '{tool_name}' from Phone to Laptop in background.")

        elif self.active_axis == DeviceType.LAPTOP and any(k in tool_name.lower() for k in phone_tool_keywords):
            target_device = DeviceType.PHONE
            logger.info(f"[DEVICE AXIS] Cross-dispatching mobile task '{tool_name}' from Laptop to Phone wirelessly.")

        return {
            "origin_axis": self.active_axis.value,
            "execution_target": target_device.value,
            "tool_name": tool_name,
            "arguments": arguments
        }
