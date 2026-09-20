"""
Emergency Kill Switch: Global hotkey handler to instantly halt all running jobs,
worker threads, and audio playback in under 1 second.
"""

import time
import threading
from typing import List, Callable, Optional
from core.config import settings
from core.logger import logger, log_latency

class KillSwitch:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KillSwitch, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, hotkey: str = settings.safety.kill_switch_hotkey):
        if self._initialized:
            return
        
        self.hotkey = hotkey
        self.is_triggered = False
        self._callbacks: List[Callable[[], None]] = []
        self._listener_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._initialized = True
        self._hook_keyboard()

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register a cleanup/halt function to run immediately upon emergency stop."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def trigger(self, source: str = "MANUAL") -> float:
        """
        Trigger emergency stop immediately across all subsystems.
        Returns execution latency in milliseconds.
        """
        start_time = time.perf_counter()
        self.is_triggered = True
        logger.critical(f"[KILL SWITCH] Emergency stop triggered from {source}! Halting all operations...")

        for cb in self._callbacks:
            try:
                cb()
            except Exception as e:
                logger.error(f"[KILL SWITCH] Error in shutdown callback: {e}")

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(f"[KILL SWITCH] Emergency shutdown completed in {duration_ms:.2f} ms (Target: < 1000 ms)")
        return duration_ms

    def reset(self) -> None:
        """Reset the kill switch to active status."""
        self.is_triggered = False
        logger.info("[KILL SWITCH] Emergency stop reset. Assistant restored to normal operation.")

    def _hook_keyboard(self) -> None:
        """Attempt global hotkey registration."""
        try:
            import keyboard
            keyboard.add_hotkey(self.hotkey, lambda: self.trigger(source=f"HOTKEY ({self.hotkey})"))
            logger.info(f"[KILL SWITCH] Global hotkey registered: '{self.hotkey}'")
        except Exception as e:
            logger.warning(f"[KILL SWITCH] Could not hook global hotkey '{self.hotkey}': {e}. Polling/API fallback active.")

    def stop_listener(self) -> None:
        """Stop hotkey listening hooks."""
        try:
            import keyboard
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
