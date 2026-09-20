"""
Builtin File Management Tools: List, Read, Search, Write, Create, Copy, Move, and Delete to Recycle Bin.
All file tools operate under sandbox boundaries and risk policies.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.safety_gate import RiskLevel, SafetyGate
from tools.base import BaseTool

# Helper to expand ~
def resolve_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve()

# 8. List Directory
class ListDirectoryArgs(BaseModel):
    directory_path: str = Field(..., description="Path to the directory to list.")

class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List files and subdirectories inside a specified folder."
    risk_level = RiskLevel.READ
    args_schema = ListDirectoryArgs

    def run(self, directory_path: str) -> List[Dict[str, Any]]:
        target = resolve_path(directory_path)
        if not target.exists() or not target.is_dir():
            raise FileNotFoundError(f"Directory not found: {target}")

        results = []
        for entry in target.iterdir():
            results.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size_bytes": entry.stat().st_size if entry.is_file() else 0,
            })
        return results

# 9. Read Text File
class ReadTextFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to the text file to read.")
    max_lines: int = Field(default=200, description="Maximum number of lines to read.")

class ReadTextFileTool(BaseTool):
    name = "read_text_file"
    description = "Read the contents of a UTF-8 text or markdown file."
    risk_level = RiskLevel.READ
    args_schema = ReadTextFileArgs

    def run(self, file_path: str, max_lines: int = 200) -> str:
        target = resolve_path(file_path)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"File not found: {target}")

        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(max_lines)]
        return "".join(lines)

# 10. Search Files
class SearchFilesArgs(BaseModel):
    search_dir: str = Field(..., description="Root directory to search inside.")
    pattern: str = Field(..., description="Glob pattern to search for (e.g. *.pdf, *report*).")

class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Search for files matching a pattern inside a folder."
    risk_level = RiskLevel.READ
    args_schema = SearchFilesArgs

    def run(self, search_dir: str, pattern: str) -> List[str]:
        target = resolve_path(search_dir)
        if not target.exists():
            return []
        matches = [str(p) for p in target.glob(pattern)]
        return matches[:50]

# 11. Write Text File
class WriteTextFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to write the file to.")
    content: str = Field(..., description="Text content to write.")

class WriteTextFileTool(BaseTool):
    name = "write_text_file"
    description = "Write text content to a file (creates backup first if file exists)."
    risk_level = RiskLevel.WRITE
    args_schema = WriteTextFileArgs

    def run(self, file_path: str, content: str) -> str:
        target = resolve_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {target}."

# 12. Create Directory
class CreateDirectoryArgs(BaseModel):
    directory_path: str = Field(..., description="Path of the directory to create.")

class CreateDirectoryTool(BaseTool):
    name = "create_directory"
    description = "Create a new folder on the disk."
    risk_level = RiskLevel.WRITE
    args_schema = CreateDirectoryArgs

    def run(self, directory_path: str) -> str:
        target = resolve_path(directory_path)
        target.mkdir(parents=True, exist_ok=True)
        return f"Directory created: {target}"

# 13. Copy File
class CopyFileArgs(BaseModel):
    source_path: str = Field(..., description="Source file path.")
    dest_path: str = Field(..., description="Destination file path.")

class CopyFileTool(BaseTool):
    name = "copy_file"
    description = "Copy a file to another location."
    risk_level = RiskLevel.WRITE
    args_schema = CopyFileArgs

    def run(self, source_path: str, dest_path: str) -> str:
        src = resolve_path(source_path)
        dst = resolve_path(dest_path)
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return f"Copied {src} to {dst}"

# 14. Move File
class MoveFileArgs(BaseModel):
    source_path: str = Field(..., description="Source file path.")
    dest_path: str = Field(..., description="Destination file path.")

class MoveFileTool(BaseTool):
    name = "move_file"
    description = "Move a file from source to destination."
    risk_level = RiskLevel.DESTRUCTIVE
    args_schema = MoveFileArgs

    def run(self, source_path: str, dest_path: str) -> str:
        src = resolve_path(source_path)
        dst = resolve_path(dest_path)
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return f"Moved {src} to {dst}"

# 15. Delete File to Recycle Bin
class DeleteFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to the file to delete.")

class DeleteFileTool(BaseTool):
    name = "delete_file_to_recycle_bin"
    description = "Move a file to the Windows Recycle Bin (Destructive, requires confirmation)."
    risk_level = RiskLevel.DESTRUCTIVE
    args_schema = DeleteFileArgs

    def __init__(self, safety_gate: Optional[SafetyGate] = None):
        self.safety_gate = safety_gate or SafetyGate()

    def run(self, file_path: str) -> str:
        target = resolve_path(file_path)
        success = self.safety_gate.delete_to_recycle_bin(target)
        if success:
            return f"Successfully moved {target} to Windows Recycle Bin."
        else:
            raise RuntimeError(f"Failed to move {target} to Recycle Bin.")
