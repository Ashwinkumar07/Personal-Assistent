"""
Builtin System Tools: Time, Date, Battery, System Resources, Active Window, and Clipboard.
"""

import time
import datetime
import psutil
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from core.safety_gate import RiskLevel
from tools.base import BaseTool

# 1. Current Time Tool
class GetCurrentTimeTool(BaseTool):
    name = "get_current_time"
    description = "Get the current system time in HH:MM:SS format."
    risk_level = RiskLevel.READ

    def run(self) -> str:
        return datetime.datetime.now().strftime("%I:%M:%S %p")

# 2. Current Date Tool
class GetCurrentDateTool(BaseTool):
    name = "get_current_date"
    description = "Get today's date in Weekday, Month DD, YYYY format."
    risk_level = RiskLevel.READ

    def run(self) -> str:
        return datetime.datetime.now().strftime("%A, %B %d, %Y")

# 3. System Specs / Resource Usage Tool
class GetSystemSpecsTool(BaseTool):
    name = "get_system_specs"
    description = "Get current CPU utilization, available RAM memory, and disk storage."
    risk_level = RiskLevel.READ

    def run(self) -> Dict[str, Any]:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "ram_available_gb": round(mem.available / (1024**3), 2),
            "ram_used_percent": mem.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
        }

# 4. Battery Status Tool
class GetBatteryStatusTool(BaseTool):
    name = "get_battery_status"
    description = "Check the laptop battery percentage and charging state."
    risk_level = RiskLevel.READ

    def run(self) -> Dict[str, Any]:
        battery = psutil.sensors_battery()
        if not battery:
            return {"has_battery": False, "message": "No battery sensor detected."}
        return {
            "has_battery": True,
            "percent": battery.percent,
            "is_plugged": battery.power_plugged,
            "time_left_minutes": round(battery.secsleft / 60) if battery.secsleft > 0 else "Charging/Calculating"
        }

# 5. Active Window Title Tool
class GetActiveWindowTitleTool(BaseTool):
    name = "get_active_window_title"
    description = "Get the title of the currently focused foreground application window."
    risk_level = RiskLevel.READ

    def run(self) -> str:
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            return title or "Unknown Foreground Window"
        except Exception:
            return "Windows GUI information unavailable."

# 6. Read Clipboard Tool
class GetClipboardTool(BaseTool):
    name = "get_clipboard"
    description = "Read the current text stored in the Windows clipboard."
    risk_level = RiskLevel.READ

    def run(self) -> str:
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            return data
        except Exception:
            return ""

# 7. Set Clipboard Tool
class SetClipboardArgs(BaseModel):
    text: str = Field(..., description="The text string to copy to the clipboard.")

class SetClipboardTool(BaseTool):
    name = "set_clipboard"
    description = "Copy given text to the Windows clipboard."
    risk_level = RiskLevel.WRITE
    args_schema = SetClipboardArgs

    def run(self, text: str) -> str:
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text)
            win32clipboard.CloseClipboard()
            return f"Successfully copied {len(text)} characters to clipboard."
        except Exception as e:
            return f"Failed to set clipboard: {e}"
