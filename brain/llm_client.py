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
        elif any(w in cmd_lower for w in ["date", "today"]):
            steps.append({"tool": "get_current_date", "args": {}, "description": "Get current date"})
        elif any(w in cmd_lower for w in ["battery", "charge"]):
            steps.append({"tool": "get_battery_status", "args": {}, "description": "Check battery"})
        elif any(w in cmd_lower for w in ["specs", "cpu", "ram", "memory"]):
            steps.append({"tool": "get_system_specs", "args": {}, "description": "Check system specs"})
        elif any(w in cmd_lower for w in ["active window", "foreground"]):
            steps.append({"tool": "get_active_window_title", "args": {}, "description": "Get active window"})
        elif "search" in cmd_lower or "google" in cmd_lower:
            query = user_command.replace("search", "").replace("google", "").strip()
            steps.append({"tool": "search_web", "args": {"query": query}, "description": f"Search web for {query}"})
        elif "download" in cmd_lower:
            steps.append({"tool": "download_file", "args": {"url": "example"}, "description": "Download requested item"})
        else:
            steps.append({"tool": "get_current_time", "args": {}, "description": "Acknowledge command"})

        return steps

    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        if self._custom_engine:
            return self._custom_engine.generate(prompt, context)
        return f"Understood: '{prompt}'. Ready to execute."
