"""
Code & Workspace Adapter:
Automates local developer workflows (Git status, Git commit, launching VS Code).
"""

import subprocess
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from core.logger import logger, log_latency
from core.safety_gate import RiskLevel
from tools.base import BaseTool
from pydantic import BaseModel, Field

class GitStatusTool(BaseTool):
    name = "get_git_status"
    description = "Check git status and modified files in the current workspace."
    risk_level = RiskLevel.READ

    def run(self) -> Dict[str, Any]:
        with log_latency("CodeAdapter.get_git_status"):
            try:
                res = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, timeout=5)
                lines = [l for l in res.stdout.splitlines() if l.strip()]
                return {"clean": len(lines) == 0, "modified_files_count": len(lines), "summary": lines[:10]}
            except Exception as e:
                return {"error": str(e)}

class OpenVSCodeArgs(BaseModel):
    folder_path: str = Field(..., description="Project folder path to open in VS Code.")

class OpenVSCodeTool(BaseTool):
    name = "open_in_vscode"
    description = "Open a project directory inside Visual Studio Code."
    risk_level = RiskLevel.WRITE
    args_schema = OpenVSCodeArgs

    def run(self, folder_path: str) -> str:
        target = Path(folder_path).resolve()
        if not target.exists():
            return f"Directory {target} does not exist."
        
        code_bin = shutil.which("code") or shutil.which("code.cmd")
        if code_bin:
            subprocess.Popen([code_bin, str(target)])
            return f"Opened {target.name} in VS Code."
        return "VS Code command ('code') not found in system PATH."
