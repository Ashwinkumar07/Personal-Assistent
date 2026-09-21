"""
Episodic, Semantic, Procedural, and Correction Memory Stores.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from memory.database import MemoryDatabase
from core.logger import logger

class MemoryManager:
    def __init__(self, db: Optional[MemoryDatabase] = None):
        self.db = db or MemoryDatabase()

    # --- EPISODIC (Dialogue & History) ---
    def record_dialogue(self, role: str, content: str, session_id: str = "default") -> None:
        conn = sqlite3.connect(self.db.db_path)
        try:
            conn.execute(
                "INSERT INTO episodic_memory (role, content, session_id) VALUES (?, ?, ?)",
                (role, content, session_id)
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent_dialogue(self, limit: int = 10) -> List[Dict[str, str]]:
        conn = sqlite3.connect(self.db.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM episodic_memory ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
        finally:
            conn.close()

    # --- SEMANTIC (User Facts & Habits) ---
    def set_fact(self, key: str, value: str, category: str = "user_preference") -> None:
        conn = sqlite3.connect(self.db.db_path)
        try:
            conn.execute(
                """
                INSERT INTO semantic_memory (category, key, value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (category, key, value)
            )
            conn.commit()
            logger.info(f"[MEMORY] Learned fact: '{key}' = '{value}'")
        finally:
            conn.close()

    def get_fact(self, key: str) -> Optional[str]:
        conn = sqlite3.connect(self.db.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM semantic_memory WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def list_all_facts(self) -> Dict[str, str]:
        conn = sqlite3.connect(self.db.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM semantic_memory")
            return {r[0]: r[1] for r in cursor.fetchall()}
        finally:
            conn.close()

    # --- PROCEDURAL (Workflows & Macros) ---
    def save_workflow(self, name: str, steps: List[Dict[str, Any]], description: str = "") -> None:
        conn = sqlite3.connect(self.db.db_path)
        try:
            conn.execute(
                """
                INSERT INTO procedural_memory (workflow_name, description, steps_json)
                VALUES (?, ?, ?)
                ON CONFLICT(workflow_name) DO UPDATE SET steps_json = excluded.steps_json, description = excluded.description
                """,
                (name, description, json.dumps(steps))
            )
            conn.commit()
            logger.info(f"[MEMORY] Saved procedural workflow: '{name}' ({len(steps)} steps)")
        finally:
            conn.close()

    def get_workflow(self, name: str) -> Optional[List[Dict[str, Any]]]:
        conn = sqlite3.connect(self.db.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT steps_json FROM procedural_memory WHERE workflow_name = ?", (name,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None
        finally:
            conn.close()

    # --- CORRECTION FEEDBACK LOOP ---
    def log_correction(self, command: str, wrong_call: str, correct_call: str, notes: str = "") -> None:
        conn = sqlite3.connect(self.db.db_path)
        try:
            conn.execute(
                """
                INSERT INTO corrections_log (user_command, wrong_tool_call, correct_tool_call, correction_notes)
                VALUES (?, ?, ?, ?)
                """,
                (command, wrong_call, correct_call, notes)
            )
            conn.commit()
            logger.info(f"[MEMORY] Recorded correction for command: '{command}'")
        finally:
            conn.close()

    def export_training_dataset(self) -> List[Dict[str, str]]:
        """Export logged corrections as synthetic fine-tuning pairs."""
        conn = sqlite3.connect(self.db.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_command, correct_tool_call FROM corrections_log")
            return [{"command": r[0], "tool_call": r[1]} for r in cursor.fetchall()]
        finally:
            conn.close()
