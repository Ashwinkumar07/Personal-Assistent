"""
Base Tool Definition: Pydantic-based schemas with risk tiers and verification contracts.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field

from core.safety_gate import RiskLevel

class BaseTool(ABC):
    name: str
    description: str
    risk_level: RiskLevel
    args_schema: Optional[Type[BaseModel]] = None

    @abstractmethod
    def run(self, **kwargs) -> Any:
        """Execute the tool logic synchronously."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Generate OpenAI/Qwen compatible JSON schema for the tool."""
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        if self.args_schema:
            schema = self.args_schema.model_json_schema()
            parameters["properties"] = schema.get("properties", {})
            parameters["required"] = schema.get("required", [])

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters,
                "risk_level": self.risk_level.value,
            }
        }
