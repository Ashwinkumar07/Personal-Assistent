"""
Automated Downloader Adapter:
Handles downloading files, research PDFs, software, and datasets safely into ~/Downloads.
"""

import os
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional
from core.config import PROJECT_ROOT
from core.logger import logger, log_latency
from core.safety_gate import RiskLevel
from tools.base import BaseTool
from pydantic import BaseModel, Field

class DownloadFileArgs(BaseModel):
    url: str = Field(..., description="Direct URL of the file to download.")
    filename: Optional[str] = Field(default=None, description="Custom filename for the downloaded file.")

class DownloaderAdapter(BaseTool):
    name = "download_file"
    description = "Download a file or document from the web to the local Downloads folder."
    risk_level = RiskLevel.WRITE
    args_schema = DownloadFileArgs

    def __init__(self, downloads_dir: Optional[Path] = None):
        self.downloads_dir = downloads_dir or Path(os.path.expanduser("~/Downloads"))
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    def run(self, url: str, filename: Optional[str] = None) -> Dict[str, Any]:
        with log_latency("Downloader.download_file", url[:30]):
            try:
                if not filename:
                    parsed_name = url.split("/")[-1].split("?")[0]
                    filename = parsed_name if parsed_name else "downloaded_file.bin"

                dest_path = self.downloads_dir / filename
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                
                with urllib.request.urlopen(req, timeout=15) as resp, open(dest_path, "wb") as out_file:
                    out_file.write(resp.read())

                file_size = dest_path.stat().st_size
                logger.info(f"[DOWNLOADER] Saved {url} to {dest_path} ({file_size} bytes)")
                return {
                    "success": True,
                    "file_path": str(dest_path),
                    "size_bytes": file_size,
                    "message": f"File downloaded successfully to {dest_path.name}."
                }
            except Exception as e:
                logger.error(f"[DOWNLOADER] Download error: {e}")
                return {"success": False, "error": str(e)}
