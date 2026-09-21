"""
Windows UI Automation Scanner:
Traverses active window control trees (buttons, text fields, lists, menus)
without brittle pixel coordinates. Uses pywin32 / UI Automation API.
"""

import os
from typing import Dict, Any, List, Optional
from core.logger import logger, log_latency

class UIAutomationScanner:
    def __init__(self):
        self._uia_available = False
        self._init_uia()

    def _init_uia(self) -> None:
        try:
            import uiautomation as auto
            self._uia_available = True
            logger.info("[AWARENESS] UIAutomation engine initialized successfully.")
        except ImportError:
            logger.debug("[AWARENESS] uiautomation package not installed. Using Win32 EnumChildWindows fallback.")

    def get_active_window_info(self) -> Dict[str, Any]:
        """Get handle, title, and bounding rectangle of the currently focused window."""
        try:
            import win32gui
            import win32process
            import psutil

            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return {"title": "Desktop / No Active Window", "hwnd": 0, "process_name": "unknown"}

            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc_name = psutil.Process(pid).name() if pid else "unknown"
            rect = win32gui.GetWindowRect(hwnd)

            return {
                "hwnd": hwnd,
                "title": title or "Untitled Window",
                "process_name": proc_name,
                "pid": pid,
                "bounds": {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3]},
            }
        except Exception as e:
            return {"title": "Desktop", "hwnd": 0, "process_name": "unknown", "error": str(e)}

    def inspect_active_controls(self, max_depth: int = 3, max_elements: int = 40) -> List[Dict[str, Any]]:
        """
        Inspect control elements (buttons, inputs, labels) of the active foreground window.
        """
        elements = []
        win_info = self.get_active_window_info()
        hwnd = win_info.get("hwnd", 0)
        if not hwnd:
            return elements

        with log_latency("UIAutomation.inspect_active_controls", win_info.get("process_name")):
            try:
                import win32gui

                def enum_child_callback(child_hwnd, extra):
                    if len(elements) >= max_elements:
                        return False
                    
                    text = win32gui.GetWindowText(child_hwnd)
                    class_name = win32gui.GetClassName(child_hwnd)
                    rect = win32gui.GetWindowRect(child_hwnd)
                    
                    if win32gui.IsWindowVisible(child_hwnd) and (text.strip() or class_name):
                        elements.append({
                            "hwnd": child_hwnd,
                            "class": class_name,
                            "text": text.strip()[:100],
                            "rect": {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3]}
                        })
                    return True

                win32gui.EnumChildWindows(hwnd, enum_child_callback, None)
            except Exception as e:
                logger.error(f"[AWARENESS] Error scanning controls: {e}")

        return elements
