import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

from core.config import PROJECT_ROOT, settings

# Ensure log directory exists
LOG_DIR = PROJECT_ROOT / settings.app.log_dir
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Application logger
log_file = LOG_DIR / "assistant.log"
latency_file = LOG_DIR / "latency.csv"
action_file = LOG_DIR / "actions.jsonl"

logging.basicConfig(
    level=getattr(logging, settings.app.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("Assistant")

# Initialize Latency CSV header if not existing
if not latency_file.exists():
    with open(latency_file, "w", encoding="utf-8") as f:
        f.write("timestamp,stage,duration_ms,metadata\n")

@contextmanager
def log_latency(stage_name: str, metadata: Optional[str] = None):
    """
    Context manager to record execution time for any processing stage.
    Logs to console/file and appends precise timing data to latency.csv.
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        meta_str = metadata.replace(",", ";") if metadata else ""
        logger.info(f"[LATENCY] {stage_name}: {duration_ms:.2f} ms {f'({metadata})' if metadata else ''}")
        with open(latency_file, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')},{stage_name},{duration_ms:.2f},{meta_str}\n")
