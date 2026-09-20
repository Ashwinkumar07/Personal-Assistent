"""
Core Orchestrator: Deterministic Python State Machine managing goal lifecycle:
Listen -> Transcribe -> Retrieve Memory -> Plan -> Safety Check -> Act -> Observe -> Verify -> Report -> Store.
Persists state in SQLite so tasks are resumable after crashes or restarts.
"""

import sqlite3
import json
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from core.config import PROJECT_ROOT, settings
from core.logger import logger, log_latency
from core.safety_gate import SafetyGate, RiskLevel
from core.kill_switch import KillSwitch
from tools.registry import ToolRegistry
from tools.builtins import register_default_tools

class OrchestratorState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    PLANNING = "PLANNING"
    SAFETY_CHECK = "SAFETY_CHECK"
    EXECUTING = "EXECUTING"
    OBSERVING = "OBSERVING"
    VERIFYING = "VERIFYING"
    REPORTING = "REPORTING"
    HALTED = "HALTED"

class StepPlan(object):
    def __init__(self, step_num: int, tool_name: str, arguments: Dict[str, Any], description: str):
        self.step_num = step_num
        self.tool_name = tool_name
        self.arguments = arguments
        self.description = description
        self.status = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
        self.result = None
        self.error = None

class Orchestrator:
    def __init__(
        self,
        db_path: Optional[Path] = None,
        registry: Optional[ToolRegistry] = None,
        safety_gate: Optional[SafetyGate] = None,
        kill_switch: Optional[KillSwitch] = None
    ):
        self.db_path = db_path or (PROJECT_ROOT / settings.app.data_dir / "orchestrator_state.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.safety_gate = safety_gate or SafetyGate()
        self.registry = registry or ToolRegistry(safety_gate=self.safety_gate)
        register_default_tools(self.registry)
        
        self.kill_switch = kill_switch or KillSwitch()
        self.kill_switch.register_callback(self._on_emergency_halt)
        
        self.current_state = OrchestratorState.IDLE
        self._init_database()

    def _init_database(self) -> None:
        """Initialize persistent state table."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    goal TEXT NOT NULL,
                    state TEXT NOT NULL,
                    plan_json TEXT,
                    current_step INTEGER DEFAULT 0,
                    final_result TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def _on_emergency_halt(self) -> None:
        """Triggered immediately when kill switch fires."""
        self.current_state = OrchestratorState.HALTED
        logger.critical("[ORCHESTRATOR] Emergency halt received! Pausing state machine.")

    def execute_plan(
        self,
        goal: str,
        steps: List[Dict[str, Any]],
        confirm_callback: Optional[Callable[[str], bool]] = None
    ) -> Dict[str, Any]:
        """
        Execute a sequential multi-step plan (capped at 5-7 steps).
        """
        if self.kill_switch.is_triggered:
            return {"success": False, "error": "System is halted by Kill Switch.", "completed_steps": 0}

        # Cap plans at 7 steps to prevent hallucination/runaway execution
        plan_steps = steps[:7]
        self.current_state = OrchestratorState.PLANNING
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO task_sessions (goal, state, plan_json) VALUES (?, ?, ?)",
                (goal, self.current_state.value, json.dumps(plan_steps))
            )
            session_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        logger.info(f"[ORCHESTRATOR] Starting Session #{session_id} for goal: '{goal}' ({len(plan_steps)} steps)")
        
        results = []
        for idx, step_data in enumerate(plan_steps):
            if self.kill_switch.is_triggered:
                logger.warning(f"[ORCHESTRATOR] Step {idx+1} aborted by Kill Switch.")
                break

            tool_name = step_data.get("tool")
            args = step_data.get("args", {})
            description = step_data.get("description", f"Step {idx+1}")

            self.current_state = OrchestratorState.SAFETY_CHECK
            logger.info(f"[ORCHESTRATOR] [Step {idx+1}/{len(plan_steps)}] {description} -> Calling '{tool_name}'")

            # Execute via Registry (enforces safety checks)
            self.current_state = OrchestratorState.EXECUTING
            exec_res = self.registry.execute(
                name=tool_name,
                arguments=args,
                confirm_callback=confirm_callback
            )

            # Observe & Verify step
            self.current_state = OrchestratorState.VERIFYING
            if not exec_res["success"]:
                logger.error(f"[ORCHESTRATOR] Step {idx+1} failed: {exec_res['error']}")
                results.append({"step": idx+1, "status": "FAILED", "error": exec_res["error"]})
                
                # Single retry attempt if configured
                logger.info(f"[ORCHESTRATOR] Attempting single self-correction retry for step {idx+1}...")
                retry_res = self.registry.execute(name=tool_name, arguments=args, confirm_callback=confirm_callback)
                if not retry_res["success"]:
                    logger.warning("[ORCHESTRATOR] Retry failed. Stopping execution and notifying user.")
                    break
                else:
                    results.append({"step": idx+1, "status": "RETRY_PASSED", "result": retry_res["result"]})
            else:
                results.append({"step": idx+1, "status": "SUCCESS", "result": exec_res["result"]})

        self.current_state = OrchestratorState.REPORTING if not self.kill_switch.is_triggered else OrchestratorState.HALTED
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "UPDATE task_sessions SET state = ?, final_result = ? WHERE id = ?",
                (self.current_state.value, json.dumps(results), session_id)
            )
            conn.commit()
        finally:
            conn.close()

        self.current_state = OrchestratorState.IDLE if not self.kill_switch.is_triggered else OrchestratorState.HALTED
        return {
            "session_id": session_id,
            "goal": goal,
            "success": all(r.get("status") in ["SUCCESS", "RETRY_PASSED"] for r in results),
            "step_results": results
        }
