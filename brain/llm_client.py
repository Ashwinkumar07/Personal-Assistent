"""
Base Brain Interface & Pluggable LLM Client:
Allows dropping in any custom LLM (GGUF, local endpoint, or custom model) seamlessly.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from core.config import settings
from core.logger import logger, log_latency

class BaseBrain(ABC):
    @abstractmethod
    def plan_steps(self, user_command: str, available_tools: List[Dict[str, Any]], context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse user command and generate sequential tool call steps."""
        pass

    @abstractmethod
    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate conversational text response."""
        pass

class PluggableLLMClient(BaseBrain):
    """
    Swappable Brain Client. By default provides deterministic rule-based tool mapping
    and is ready to connect to your custom-trained LLM.
    """
    def __init__(self, model_path: Optional[str] = settings.brain.model_path):
        self.model_path = model_path
        self._custom_engine = None
        logger.info(f"[BRAIN] Pluggable LLM Interface initialized (Custom Model Slot: '{self.model_path}').")

    def attach_custom_engine(self, engine_callable: Any) -> None:
        """Attach your own custom-trained LLM inference engine."""
        self._custom_engine = engine_callable
        logger.info("[BRAIN] Custom LLM engine successfully attached!")

    def plan_steps(self, user_command: str, available_tools: List[Dict[str, Any]], context: Optional[str] = None) -> List[Dict[str, Any]]:
        if self._custom_engine:
            return self._custom_engine(user_command, available_tools, context)

        # Fallback intelligent command mapper for immediate testing before custom model is loaded
        cmd_lower = user_command.lower().strip()
        steps = []

        if any(w in cmd_lower for w in ["time", "clock"]):
            steps.append({"tool": "get_current_time", "args": {}, "description": "Get current time"})
        elif any(w in cmd_lower for w in ["date", "day", "today"]):
            steps.append({"tool": "get_current_date", "args": {}, "description": "Get current date"})
        elif any(w in cmd_lower for w in ["battery", "charge", "plugged"]):
            if "phone" in cmd_lower or "mobile" in cmd_lower:
                steps.append({"tool": "get_phone_status", "args": {}, "description": "Check phone battery"})
            else:
                steps.append({"tool": "get_battery_status", "args": {}, "description": "Check battery"})
        elif any(w in cmd_lower for w in ["specs", "cpu", "ram", "memory", "disk"]):
            steps.append({"tool": "get_system_specs", "args": {}, "description": "Check system specs"})
        elif any(w in cmd_lower for w in ["active window", "foreground", "window", "focused", "what app"]):
            steps.append({"tool": "get_active_window_title", "args": {}, "description": "Get active window"})
        elif any(w in cmd_lower for w in ["phone", "android", "mobile"]):
            steps.append({"tool": "get_phone_status", "args": {}, "description": "Check phone status"})
        elif any(w in cmd_lower for w in ["list", "show me what is inside"]) and any(w in cmd_lower for w in ["desktop", "documents", "downloads", "files", "folder"]):
            steps.append({"tool": "list_directory", "args": {"directory_path": "~/Desktop"}, "description": "List directory"})
        elif any(w in cmd_lower for w in ["search for", "find files", "find all"]):
            steps.append({"tool": "search_files", "args": {"search_dir": "~/Desktop", "pattern": "*.*"}, "description": "Search files"})
        elif any(w in cmd_lower for w in ["read", "show me the first"]):
            steps.append({"tool": "read_text_file", "args": {"file_path": "notes.txt"}, "description": "Read file"})
        elif any(w in cmd_lower for w in ["create a new folder", "make a folder"]):
            steps.append({"tool": "create_directory", "args": {"directory_path": "NewFolder"}, "description": "Create folder"})
        elif any(w in cmd_lower for w in ["copy", "make a copy"]):
            if "clipboard" in cmd_lower:
                steps.append({"tool": "set_clipboard", "args": {"text": "text"}, "description": "Copy to clipboard"})
            else:
                steps.append({"tool": "copy_file", "args": {"source_path": "a", "dest_path": "b"}, "description": "Copy file"})
        elif any(w in cmd_lower for w in ["move", "transfer"]):
            steps.append({"tool": "move_file", "args": {"source_path": "a", "dest_path": "b"}, "description": "Move file"})
        elif any(w in cmd_lower for w in ["delete", "remove"]):
            steps.append({"tool": "delete_file_to_recycle_bin", "args": {"file_path": "a"}, "description": "Delete file to recycle bin"})
        elif any(w in cmd_lower for w in ["write", "save"]) and "note" in cmd_lower:
            steps.append({"tool": "write_text_file", "args": {"file_path": "todo.txt", "content": "note"}, "description": "Write text file"})
        elif "clipboard" in cmd_lower:
            if any(w in cmd_lower for w in ["copy", "set"]):
                steps.append({"tool": "set_clipboard", "args": {"text": "text"}, "description": "Set clipboard"})
            else:
                steps.append({"tool": "get_clipboard", "args": {}, "description": "Get clipboard"})
        elif any(w in cmd_lower for w in ["search", "google", "weather", "look up", "find doc", "find stock"]):
            query = user_command.replace("search", "").replace("google", "").strip()
            steps.append({"tool": "search_web", "args": {"query": query}, "description": f"Search web for {query}"})
        elif "download" in cmd_lower:
            steps.append({"tool": "download_file", "args": {"url": "https://example.com/file"}, "description": "Download requested item"})
        else:
            steps.append({"tool": "get_current_time", "args": {}, "description": "Acknowledge command"})

        return steps

    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        if self._custom_engine:
            return self._custom_engine.generate(prompt, context)
        return f"Understood: '{prompt}'. Ready to execute."
