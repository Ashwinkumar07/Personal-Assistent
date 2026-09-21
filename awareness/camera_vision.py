"""
Camera Vision Module:
Handles on-demand frame capture from webcam or local IP/wireless stream.
Supports saving moments, reading physical documents, and passing frames to vision models.
Strict Privacy: Camera is strictly on-demand, frames remain 100% local, and halts with kill switch.
"""

import time
from pathlib import Path
from typing import Optional, Tuple, Any
from core.config import PROJECT_ROOT
from core.logger import logger, log_latency
from core.kill_switch import KillSwitch

class CameraVision:
    def __init__(self, camera_index: int = 0, moments_dir: Optional[Path] = None):
        self.camera_index = camera_index
        self.moments_dir = moments_dir or (PROJECT_ROOT / "data" / "moments")
        self.moments_dir.mkdir(parents=True, exist_ok=True)
        self.kill_switch = KillSwitch()
        self.kill_switch.register_callback(self.release_camera)
        self._cv2 = None
        self._init_cv2()

    def _init_cv2(self) -> None:
        try:
            import cv2
            self._cv2 = cv2
            logger.info("[CAMERA] OpenCV backend initialized.")
        except ImportError:
            logger.debug("[CAMERA] OpenCV not installed. Camera vision running in mock/offline mode.")

    def capture_frame(self) -> Optional[Any]:
        """Capture a single frame from the camera as a numpy array."""
        if self.kill_switch.is_triggered or self._cv2 is None:
            return None

        with log_latency("Camera.capture_frame", f"CamIndex:{self.camera_index}"):
            try:
                cap = self._cv2.VideoCapture(self.camera_index)
                if not cap.isOpened():
                    logger.warning(f"[CAMERA] Unable to open camera index {self.camera_index}.")
                    return None
                
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    return frame
            except Exception as e:
                logger.error(f"[CAMERA] Frame capture error: {e}")
        return None

    def save_moment(self, description: str = "moment") -> Optional[Path]:
        """
        Capture and save a moment snapshot to the local moments directory.
        """
        frame = self.capture_frame()
        if frame is None or self._cv2 is None:
            return None

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        clean_desc = "".join(c for c in description if c.isalnum() or c in ("-", "_"))[:30]
        filename = f"{clean_desc}_{timestamp}.jpg"
        save_path = self.moments_dir / filename

        try:
            self._cv2.imwrite(str(save_path), frame)
            logger.info(f"[CAMERA] Moment saved to {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"[CAMERA] Failed to save moment: {e}")
            return None

    def release_camera(self) -> None:
        """Release camera resources immediately on emergency halt."""
        logger.info("[CAMERA] Releasing camera hardware.")
