"""
==============================================================================
Cognitive Learning & Reasoning Engine (System 1 + System 2)
==============================================================================
Implements:
1. Fast Intent & Semantic Parser (System 1)
2. Dynamic In-Context Few-Shot Memory Retrieval (System 2)
3. Active Doubts & Clarification Generator
4. Procedural Workflow / Macro Compiler ("When I say X, do Y and Z")
5. Verbal Self-Reflection & Mistake Attribution (Reflexion Paradigm)
==============================================================================
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from core.logger import logger
from core.user_identity import UserIdentity
from core.self_reflection import SelfReflectionEngine
from memory.manager import MemoryManager

class CognitiveEngine:
    """
    Advanced cognitive orchestrator that coordinates memory retrieval,
    few-shot contextual demonstration injection, procedural workflows,
    and adaptive learning loops.
    """

    def __init__(
        self,
        user_identity: Optional[UserIdentity] = None,
        reflection_engine: Optional[SelfReflectionEngine] = None,
        memory_manager: Optional[MemoryManager] = None
    ):
        self.identity = user_identity or UserIdentity()
        self.reflection = reflection_engine or SelfReflectionEngine()
        self.memory = memory_manager or MemoryManager()

    def parse_and_learn_workflow(self, text: str) -> Optional[str]:
        """
        Detect and compile procedural workflows (e.g., "When I say X, do Y and Z").
        """
        match = re.search(r'when\s+i\s+say\s+[\'"]?([^\'",]+)[\'"]?,\s*(?:always\s+)?(?:do\s+|run\s+)?(.+)', text, re.IGNORECASE)
        if match:
            trigger_phrase = match.group(1).strip().lower()
            actions_str = match.group(2).strip()
            
            # Decompose actions by 'and', 'then', commas
            action_parts = [p.strip() for p in re.split(r'\band\b|\bthen\b|,', actions_str) if p.strip()]
            
            steps = []
            for act in action_parts:
                steps.append({"action": act, "description": act.capitalize()})

            self.memory.save_workflow(
                name=trigger_phrase,
                steps=steps,
                description=f"Auto-compiled workflow for '{trigger_phrase}'"
            )
            name = self.identity.display_name
            return f"Understood, {name}! I have created a new automated workflow for \"{trigger_phrase}\" with {len(steps)} action(s): {', '.join(action_parts)}."
        return None

    def retrieve_relevant_context(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Dynamic Few-Shot In-Context Memory Retrieval.
        Ranks facts, learned rules, and past corrections by lexical similarity and relevance.
        """
        q_lower = query.lower()
        query_words = set(re.findall(r'\b[a-z0-9_]+\b', q_lower))

        # 1. Search Semantic Memory Facts
        all_facts = self.memory.list_all_facts()
        scored_facts: List[Tuple[float, str, str]] = []
        for key, val in all_facts.items():
            val_words = set(re.findall(r'\b[a-z0-9_]+\b', val.lower() + " " + key.lower()))
            overlap = len(query_words & val_words)
            if overlap > 0 or key.lower() in q_lower:
                score = overlap + (2.0 if key.lower() in q_lower else 0.0)
                scored_facts.append((score, key, val))
        
        scored_facts.sort(key=lambda x: x[0], reverse=True)
        top_facts = [f[2] for f in scored_facts[:top_k]]

        # 2. Search Self-Reflection Learned Rules
        relevant_rules = self.reflection.get_relevant_rules(query)
        top_rules = [r["instruction"] for r in relevant_rules[:top_k]]

        # 3. Check for matching Procedural Workflow
        matching_workflow = None
        for wf_name in [q_lower, q_lower.strip('."\'')]:
            wf = self.memory.get_workflow(wf_name)
            if wf:
                matching_workflow = {"name": wf_name, "steps": wf}
                break

        return {
            "facts": top_facts,
            "rules": top_rules,
            "workflow": matching_workflow
        }

    def detect_clarification_need(self, command: str) -> Optional[str]:
        """
        Active Doubt & Clarification Engine:
        Detects ambiguous, underspecified, or risky commands and returns a clarifying question.
        """
        cmd_lower = command.lower().strip()
        name = self.identity.display_name

        # Ambiguous delete without target
        if cmd_lower in ("delete file", "delete files", "remove file", "clean"):
            return f"{name}, which specific file or folder would you like me to delete? Please specify the name or path."

        # Ambiguous search without query
        if cmd_lower in ("search", "search for", "google", "look up"):
            return f"What specific topic or query would you like me to search for, {name}?"

        # Ambiguous download without URL
        if cmd_lower in ("download", "download file", "download this"):
            return f"Please provide the download link or URL, {name}."

        # Ambiguous write without filename
        if cmd_lower in ("write note", "save note", "make note", "write text"):
            return f"What content or note would you like me to write, and should I save it to Notes.txt or Word?"

        return None

    def verbal_reflexion_critique(self, command: str, failed_tool: str, error_msg: str) -> str:
        """
        Verbal Reflexion synthesis when an action encounters an obstacle.
        """
        analysis = self.reflection.analyze_and_record_failure(
            goal=command,
            tool_name=failed_tool,
            args={},
            error_msg=error_msg
        )
        return analysis.get("rule", f"Learned from error: {error_msg}")
