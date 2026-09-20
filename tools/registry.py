"""
Tool Registry: Central catalog for discovering, validating, and executing tools with the Safety Gate.
"""

from typing import Dict, List, Optional, Any
from core.safety_gate import SafetyGate, RiskLevel
from core.logger import logger, log_latency
from tools.base import BaseTool

class ToolRegistry:
    def __init__(self, safety_gate: Optional[SafetyGate] = None):
        self._tools: Dict[str, BaseTool] = {}
        self.safety_gate = safety_gate or SafetyGate()

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        if tool.name in self._tools:
            logger.warning(f"[REGISTRY] Overwriting existing tool: '{tool.name}'")
        self._tools[tool.name] = tool
        logger.info(f"[REGISTRY] Registered tool '{tool.name}' [Risk: {tool.risk_level.value}]")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        return [tool.get_schema() for tool in self._tools.values()]

    def execute(
        self,
        name: str,
        arguments: Dict[str, Any],
        confirm_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool by name with Safety Gate authorization and audit logging.
        """
        tool = self.get_tool(name)
        if not tool:
            err = f"Tool '{name}' not found in registry."
            logger.error(f"[REGISTRY] {err}")
            return {"success": False, "error": err, "result": None}

        # 1. Authorize via Safety Gate
        try:
            authorized = self.safety_gate.evaluate_and_authorize(
                tool_name=tool.name,
                risk_level=tool.risk_level,
                arguments=arguments,
                confirm_callback=confirm_callback
            )
            if not authorized:
                self.safety_gate.log_action(
                    tool_name=tool.name,
                    risk_level=tool.risk_level,
                    arguments=arguments,
                    result=None,
                    confirmed=False,
                    error="Action cancelled by user confirmation."
                )
                return {"success": False, "error": "Action rejected by user confirmation.", "result": None}
        except Exception as e:
            self.safety_gate.log_action(
                tool_name=tool.name,
                risk_level=tool.risk_level,
                arguments=arguments,
                result=None,
                confirmed=False,
                error=str(e)
            )
            return {"success": False, "error": str(e), "result": None}

        # 2. Validate parameters against Pydantic args_schema if present
        validated_args = arguments
        if tool.args_schema:
            try:
                model_inst = tool.args_schema(**arguments)
                validated_args = model_inst.model_dump()
            except Exception as e:
                err_msg = f"Invalid arguments for tool '{name}': {e}"
                logger.error(f"[REGISTRY] {err_msg}")
                self.safety_gate.log_action(
                    tool_name=tool.name,
                    risk_level=tool.risk_level,
                    arguments=arguments,
                    result=None,
                    confirmed=True,
                    error=err_msg
                )
                return {"success": False, "error": err_msg, "result": None}

        # 3. Execute tool
        with log_latency(f"Tool.{tool.name}", str(validated_args)[:40]):
            try:
                result = tool.run(**validated_args)
                self.safety_gate.log_action(
                    tool_name=tool.name,
                    risk_level=tool.risk_level,
                    arguments=validated_args,
                    result=result,
                    confirmed=True,
                    error=None
                )
                return {"success": True, "error": None, "result": result}
            except Exception as e:
                err_msg = f"Error executing tool '{name}': {e}"
                logger.error(f"[REGISTRY] {err_msg}")
                self.safety_gate.log_action(
                    tool_name=tool.name,
                    risk_level=tool.risk_level,
                    arguments=validated_args,
                    result=None,
                    confirmed=True,
                    error=err_msg
                )
                return {"success": False, "error": err_msg, "result": None}
