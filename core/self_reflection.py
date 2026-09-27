"""
==============================================================================
Self-Reflection & Continuous Mistake-Learning Engine
==============================================================================
Enables the assistant to:
1. Intercept errors and failed tool executions.
2. Formulate root-cause analyses and derive 'Learned Rules'.
3. Persist mistakes and rules in an offline SQLite reflection database.
4. Dynamically inject learned lessons into future command planning.
5. Continuously adapt so tomorrow's execution is smarter than today's.
==============================================================================
"""

import sqlite3
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.config import PROJECT_ROOT
from core.logger import logger

class SelfReflectionEngine:
    """Manages failure reflection, error attribution, and autonomous rule learning."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (PROJECT_ROOT / "data" / "reflections.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite tables for mistakes, learned rules, and task reflections."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS mistakes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_goal TEXT NOT NULL,
                    failed_tool TEXT NOT NULL,
                    arguments_json TEXT,
                    error_message TEXT NOT NULL,
                    context_json TEXT,
                    root_cause TEXT,
                    corrective_action TEXT
                );

                CREATE TABLE IF NOT EXISTS learned_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_keyword TEXT NOT NULL UNIQUE,
                    rule_instruction TEXT NOT NULL,
                    preferred_tool TEXT,
                    default_args_json TEXT,
                    success_count INTEGER DEFAULT 1,
                    last_applied TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS daily_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_str TEXT NOT NULL UNIQUE,
                    summary_text TEXT NOT NULL,
                    mistakes_count INTEGER DEFAULT 0,
                    rules_learned INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        finally:
            conn.close()

    def analyze_and_record_failure(
        self,
        goal: str,
        tool_name: str,
        args: Dict[str, Any],
        error_msg: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Analyze a failed tool call, infer root cause, and formulate a learned rule.
        """
        # 1. Deterministic Root-Cause Inference
        err_lower = error_msg.lower()
        root_cause = "Unknown Execution Failure"
        corrective_action = "Verify command syntax and tool arguments."
        rule_keyword = goal.strip().split()[0].lower() if goal else tool_name

        if "not found" in err_lower or "no such file" in err_lower:
            root_cause = "File or resource path does not exist."
            corrective_action = "Validate path existence before calling or prompt for path clarification."
        elif "permission" in err_lower or "access is denied" in err_lower:
            root_cause = "Insufficient system privileges or file locked by another process."
            corrective_action = "Run with elevated privileges or release file lock."
        elif "timeout" in err_lower or "timed out" in err_lower:
            root_cause = "Process or network operation took too long."
            corrective_action = "Increase timeout threshold or run as background task."
        elif "invalid argument" in err_lower or "missing argument" in err_lower or "typeerror" in err_lower:
            root_cause = "Incorrect parameter format provided to tool."
            corrective_action = "Enforce strict schema validation before dispatching tool."
        else:
            root_cause = f"Runtime tool failure: {error_msg}"
            corrective_action = "Retry with fallback parameters or alternative tool."

        # 2. Record to Mistakes Table
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO mistakes (user_goal, failed_tool, arguments_json, error_message, context_json, root_cause, corrective_action)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (goal, tool_name, json.dumps(args), error_msg, json.dumps(context or {}), root_cause, corrective_action)
            )
            mistake_id = cursor.lastrowid

            # 3. Create or Update Learned Rule
            rule_text = f"When handling '{goal}', avoid failure '{error_msg}'. Action: {corrective_action}"
            cursor.execute(
                """
                INSERT INTO learned_rules (pattern_keyword, rule_instruction, preferred_tool, default_args_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(pattern_keyword) DO UPDATE SET
                    rule_instruction = excluded.rule_instruction,
                    last_applied = CURRENT_TIMESTAMP
                """,
                (rule_keyword, rule_text, tool_name, json.dumps(args))
            )
            conn.commit()
            logger.info(f"[SELF-REFLECTION] Recorded Mistake #{mistake_id} & Learned Rule for '{rule_keyword}': {rule_text}")
        finally:
            conn.close()

        return {
            "root_cause": root_cause,
            "corrective_action": corrective_action,
            "rule": rule_text
        }

    def record_manual_correction(self, wrong_command: str, correct_command: str, feedback: str = "") -> None:
        """Allow user to teach the assistant a direct correction."""
        keyword = wrong_command.strip().lower()
        rule_text = f"User corrected: '{wrong_command}' -> should be handled as '{correct_command}'. Notes: {feedback}"
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO learned_rules (pattern_keyword, rule_instruction)
                VALUES (?, ?)
                ON CONFLICT(pattern_keyword) DO UPDATE SET
                    rule_instruction = excluded.rule_instruction,
                    success_count = success_count + 1,
                    last_applied = CURRENT_TIMESTAMP
                """,
                (keyword, rule_text)
            )
            conn.commit()
            logger.info(f"[SELF-REFLECTION] Learned direct user correction for '{keyword}'")
        finally:
            conn.close()

    def get_relevant_rules(self, user_command: str) -> List[Dict[str, Any]]:
        """Find any learned rules or past mistake guidance relevant to the given command."""
        cmd_lower = user_command.lower().strip()
        words = set(re.findall(r'\w+', cmd_lower))
        
        conn = sqlite3.connect(self.db_path)
        relevant_rules = []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT pattern_keyword, rule_instruction, preferred_tool, default_args_json, success_count FROM learned_rules")
            rows = cursor.fetchall()
            for kw, rule_inst, pref_tool, args_json, sc in rows:
                if kw in cmd_lower or any(w in kw for w in words):
                    relevant_rules.append({
                        "keyword": kw,
                        "instruction": rule_inst,
                        "preferred_tool": pref_tool,
                        "default_args": json.loads(args_json) if args_json else {},
                        "confidence": sc
                    })
        finally:
            conn.close()
        return relevant_rules

    def record_success(self, keyword: str) -> None:
        """Increment confidence on a learned rule when an execution succeeds."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                UPDATE learned_rules 
                SET success_count = success_count + 1, last_applied = CURRENT_TIMESTAMP
                WHERE pattern_keyword = ?
                """,
                (keyword.lower(),)
            )
            conn.commit()
        finally:
            conn.close()

    def generate_daily_reflection(self) -> str:
        """Summarize today's learning progress and self-reflections."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM mistakes WHERE date(timestamp) = date('now')"
            )
            mistakes_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM learned_rules WHERE date(created_at) = date('now')"
            )
            new_rules = cursor.fetchone()[0]

            cursor.execute(
                "SELECT pattern_keyword, rule_instruction FROM learned_rules ORDER BY last_applied DESC LIMIT 3"
            )
            recent_rules = cursor.fetchall()
        finally:
            conn.close()

        reflection = (
            f"Daily Reflection ({today_str}): "
            f"Encountered {mistakes_count} execution error(s) and internalized {new_rules} new rule(s). "
        )
        if recent_rules:
            rules_str = "; ".join([f"[{r[0]}]: {r[1]}" for r in recent_rules])
            reflection += f"Active adaptations: {rules_str}"
        else:
            reflection += "Operating with zero unhandled errors."

        return reflection
