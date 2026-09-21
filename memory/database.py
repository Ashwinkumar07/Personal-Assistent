"""
Memory Database:
SQLite schemas for 3-tier memory: Episodic (conversations), Semantic (user facts),
Procedural (workflows), and Correction feedback logs.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from core.config import PROJECT_ROOT, settings

class MemoryDatabase:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (PROJECT_ROOT / settings.memory.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    def _init_tables(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            # 1. Episodic Memory (Rolling conversations)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 2. Semantic Memory (User facts & preferences)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 3. Procedural Memory (Learned workflows & macros)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS procedural_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    steps_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 4. Correction Feedback (Continuous learning dataset)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS corrections_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_command TEXT NOT NULL,
                    wrong_tool_call TEXT,
                    correct_tool_call TEXT NOT NULL,
                    correction_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()
