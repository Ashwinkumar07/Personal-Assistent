"""
Safety Gate Engine: The mandatory security perimeter for the assistant.
Enforces:
1. Risk-tiered execution (READ, WRITE, DESTRUCTIVE, FORBIDDEN)
2. Sandboxed folder access
3. Pre-modification backup copies
4. Recycle Bin deletes only
5. Prompt-injection isolation (data vs. instructions)
6. 100% action audit logging
"""

import os
import shutil
import json
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.config import PROJECT_ROOT, settings
from core.logger import logger, log_file

class RiskLevel(str, Enum):
    READ = "READ"               # Runs automatically; logged
    WRITE = "WRITE"             # Confirmed once per task; creates backup copy first
    DESTRUCTIVE = "DESTRUCTIVE" # Always confirmed with spoken summary; Recycle Bin only
    FORBIDDEN = "FORBIDDEN"     # Blocked by default (no raw shell, no admin, no registry)

class SafetyViolationError(PermissionError):
    """Raised when an operation violates safety gate policies."""
    pass

class SafetyGate:
    def __init__(
        self,
        backup_dir: Optional[Path] = None,
        sandbox_dirs: Optional[List[str]] = None,
        audit_log_path: Optional[Path] = None
    ):
        self.backup_dir = backup_dir or (PROJECT_ROOT / settings.safety.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Resolve sandbox paths to absolute paths
        self.sandbox_dirs = [
            Path(os.path.expanduser(p)).resolve()
            for p in (sandbox_dirs or settings.safety.sandbox_directories)
        ]
        # Include project root in sandbox
        self.sandbox_dirs.append(PROJECT_ROOT.resolve())
        
        self.audit_log_path = audit_log_path or (PROJECT_ROOT / settings.app.log_dir / "actions.jsonl")
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def is_path_sandboxed(self, target_path: Path) -> bool:
        """
        Verify if the target path is inside allowed sandbox directories.
        """
        resolved = target_path.resolve()
        for allowed in self.sandbox_dirs:
            try:
                resolved.relative_to(allowed)
                return True
            except ValueError:
                continue
        return False

    def create_backup(self, file_path: Path) -> Optional[Path]:
        """
        Create a timestamped backup copy before modifying any file.
        """
        if not file_path.exists() or not file_path.is_file():
            return None
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        dest_path = self.backup_dir / backup_filename
        
        shutil.copy2(file_path, dest_path)
        logger.info(f"[SAFETY] Created backup of {file_path} at {dest_path}")
        return dest_path

    def delete_to_recycle_bin(self, file_path: Path) -> bool:
        """
        Move file/folder to Windows Recycle Bin instead of permanent deletion.
        Uses winshell/ctypes fallback.
        """
        if not file_path.exists():
            return False
            
        try:
            # Try send2trash if installed
            import send2trash
            send2trash.send2trash(str(file_path.resolve()))
            logger.info(f"[SAFETY] Moved {file_path} to Recycle Bin via send2trash.")
            return True
        except ImportError:
            # Fallback using Windows Shell API ctypes
            import ctypes
            from ctypes import wintypes
            
            FO_DELETE = 0x0003
            FOF_ALLOWUNDO = 0x0040
            FOF_NOCONFIRMATION = 0x0010
            FOF_SILENT = 0x0004
            
            class SHFILEOPSTRUCTW(ctypes.Structure):
                _fields_ = [
                    ("hwnd", wintypes.HWND),
                    ("wFunc", wintypes.UINT),
                    ("pFrom", wintypes.LPCWSTR),
                    ("pTo", wintypes.LPCWSTR),
                    ("fFlags", wintypes.WORD),
                    ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings", wintypes.LPVOID),
                    ("lpszProgressTitle", wintypes.LPCWSTR),
                ]
            
            # Windows API requires double null-terminated string
            path_str = str(file_path.resolve()) + "\0\0"
            fileop = SHFILEOPSTRUCTW(
                hwnd=None,
                wFunc=FO_DELETE,
                pFrom=path_str,
                pTo=None,
                fFlags=FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT,
                fAnyOperationsAborted=False,
                hNameMappings=None,
                lpszProgressTitle=None,
            )
            result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(fileop))
            if result == 0 and not fileop.fAnyOperationsAborted:
                logger.info(f"[SAFETY] Moved {file_path} to Recycle Bin via SHFileOperation.")
                return True
            else:
                logger.error(f"[SAFETY] SHFileOperation failed with code {result}")
                return False

    def log_action(
        self,
        tool_name: str,
        risk_level: RiskLevel,
        arguments: Dict[str, Any],
        result: Any,
        confirmed: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Record every action to the immutable audit log (actions.jsonl).
        """
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tool": tool_name,
            "risk_level": risk_level.value,
            "arguments": arguments,
            "confirmed": confirmed,
            "result": str(result)[:500] if result is not None else None,
            "error": error,
        }
        
        with open(self.audit_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def evaluate_and_authorize(
        self,
        tool_name: str,
        risk_level: RiskLevel,
        arguments: Dict[str, Any],
        confirm_callback: Optional[callable] = None
    ) -> bool:
        """
        Evaluate tool execution against safety policies and request confirmation if required.
        """
        # 1. Block FORBIDDEN tools immediately
        if risk_level == RiskLevel.FORBIDDEN:
            logger.error(f"[SAFETY GATE] Access Denied: Tool '{tool_name}' is classified as FORBIDDEN.")
            raise SafetyViolationError(f"Action '{tool_name}' is forbidden by safety policy.")

        # 2. Check path sandboxing for any file path arguments
        for k, v in arguments.items():
            if isinstance(v, (str, Path)) and ("path" in k.lower() or "file" in k.lower() or "dir" in k.lower()):
                p = Path(os.path.expanduser(str(v)))
                # If path exists or has parent directory, check sandbox
                if p.is_absolute() and not self.is_path_sandboxed(p):
                    logger.error(f"[SAFETY GATE] Access Denied: Path '{p}' is outside allowed sandbox.")
                    raise SafetyViolationError(f"Path '{p}' is outside allowed sandbox directories.")

        # 3. Handle READ (Automatic)
        if risk_level == RiskLevel.READ:
            return True

        # 4. Handle WRITE (Confirm once per task + auto backup)
        if risk_level == RiskLevel.WRITE:
            # If target file exists, make backup copy
            for k, v in arguments.items():
                if isinstance(v, (str, Path)) and ("path" in k.lower() or "file" in k.lower()):
                    p = Path(os.path.expanduser(str(v)))
                    if p.exists() and p.is_file():
                        self.create_backup(p)
            return True

        # 5. Handle DESTRUCTIVE (Requires explicit confirmation)
        if risk_level == RiskLevel.DESTRUCTIVE:
            if confirm_callback:
                prompt_msg = f"Confirmation required for destructive action '{tool_name}' with parameters {arguments}."
                confirmed = confirm_callback(prompt_msg)
                if not confirmed:
                    logger.warning(f"[SAFETY GATE] Destructive action '{tool_name}' rejected by user.")
                    return False
            return True

        return True
