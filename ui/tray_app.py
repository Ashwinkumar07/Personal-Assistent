"""
System Tray Control Panel:
Lightweight Windows notification area icon with status monitoring and 1-click Emergency Stop.
"""

from typing import Optional, Callable
import threading
from core.logger import logger
from core.kill_switch import KillSwitch

class SystemTrayApp:
    def __init__(self, kill_switch: Optional[KillSwitch] = None, on_exit_callback: Optional[Callable[[], None]] = None):
        self.kill_switch = kill_switch or KillSwitch()
        self.on_exit_callback = on_exit_callback
        self._icon = None
        self._thread = None

    def _create_image(self):
        try:
            from PIL import Image, ImageDraw
            # Generate a clean circular icon
            width, height = 64, 64
            image = Image.new("RGB", (width, height), color=(240, 240, 240))
            dc = ImageDraw.Draw(image)
            dc.ellipse([(8, 8), (56, 56)], fill=(33, 150, 243))
            return image
        except ImportError:
            return None

    def _emergency_stop(self, icon, item):
        logger.critical("[TRAY APP] Emergency stop triggered from tray menu!")
        self.kill_switch.trigger(source="TRAY_ICON")

    def _on_exit(self, icon, item):
        logger.info("[TRAY APP] Exiting assistant...")
        if self.on_exit_callback:
            self.on_exit_callback()
        if self._icon:
            self._icon.stop()

    def run_in_background(self) -> None:
        """Start tray icon in background thread if pystray is installed."""
        try:
            import pystray
            img = self._create_image()
            if img:
                menu = pystray.Menu(
                    pystray.MenuItem("Assistant: Online", lambda icon, item: None, enabled=False),
                    pystray.MenuItem("Emergency Stop (Kill Switch)", self._emergency_stop),
                    pystray.MenuItem("Exit", self._on_exit)
                )
                self._icon = pystray.Icon("LocalAssistant", img, "Local Desktop Assistant", menu)
                self._thread = threading.Thread(target=self._icon.run, daemon=True, name="TrayApp")
                self._thread.start()
                logger.info("[TRAY APP] System tray icon running.")
        except Exception as e:
            logger.debug(f"[TRAY APP] Tray initialization skipped: {e}")
