"""
==============================================================================
Adaptive Local Brain:
Merges User Identity, Desktop Perception, and Learned Mistake Rules
into Deterministic & Quantized Execution Plans.
==============================================================================
"""

import re
from typing import Dict, Any, List, Optional
from core.config import settings
from core.logger import logger
from core.user_identity import UserIdentity
from core.self_reflection import SelfReflectionEngine
from brain.llm_client import BaseBrain

class AdaptiveLocalBrain(BaseBrain):
    """
    Intelligent, private local brain that adapts its decisions based on:
    - User Identity & Preferences (Aswin)
    - Active Desktop Environment (Foreground App, Clipboard)
    - Learned Rules from Past Mistakes (Self-Reflection Database)
    """

    def __init__(
        self,
        user_identity: Optional[UserIdentity] = None,
        reflection_engine: Optional[SelfReflectionEngine] = None
    ):
        self.identity = user_identity or UserIdentity()
        self.reflection = reflection_engine or SelfReflectionEngine()
        logger.info(f"[ADAPTIVE BRAIN] Initialized for {self.identity.user_name} with Self-Reflection active.")

    def plan_steps(
        self,
        user_command: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Deconstructs user command into sequential, safety-gated tool steps
        guided by user profile and learned mistake rules.
        """
        cmd_lower = user_command.lower().strip()
        context = context or {}
        active_window = context.get("active_window", "")
        clipboard = context.get("clipboard", "")

        # 1. Check for relevant Learned Rules from past mistakes
        learned_rules = self.reflection.get_relevant_rules(user_command)
        if learned_rules:
            logger.info(f"[ADAPTIVE BRAIN] Applied {len(learned_rules)} learned rule(s) for command '{user_command}'.")

        steps: List[Dict[str, Any]] = []

        # 2. Match Explicit Direct Commands & Desktop Tools

        # Time & Date
        if any(w in cmd_lower for w in ["time", "clock"]):
            steps.append({"tool": "get_current_time", "args": {}, "description": "Check current time"})
        elif any(w in cmd_lower for w in ["date", "today", "calendar"]):
            steps.append({"tool": "get_current_date", "args": {}, "description": "Check current date"})

        # System Telemetry & Performance
        elif any(w in cmd_lower for w in ["battery", "charge", "power"]):
            steps.append({"tool": "get_battery_status", "args": {}, "description": "Check system battery"})
        elif any(w in cmd_lower for w in ["spec", "specs", "cpu", "ram", "memory", "hardware"]):
            steps.append({"tool": "get_system_specs", "args": {}, "description": "Check hardware telemetry"})
        elif any(w in cmd_lower for w in ["active window", "foreground", "current app", "what am i looking at"]):
            steps.append({"tool": "get_active_window_title", "args": {}, "description": "Inspect active application window"})

        # Web Search & Browser Automation
        elif "search" in cmd_lower or "google" in cmd_lower or "browse" in cmd_lower:
            query = user_command
            for word in ["search for", "search", "google", "look up", "find"]:
                if query.lower().startswith(word):
                    query = query[len(word):].strip()
            steps.append({"tool": "search_web", "args": {"query": query}, "description": f"Search web for '{query}'"})

        # Code & Dev Tools
        elif "git status" in cmd_lower or "repo status" in cmd_lower:
            steps.append({"tool": "git_status", "args": {}, "description": "Check Git repository status"})
        elif "open vscode" in cmd_lower or "open code" in cmd_lower or "launch editor" in cmd_lower:
            steps.append({"tool": "open_vscode", "args": {}, "description": "Launch Visual Studio Code"})

        # Office / Document Creation
        elif "word" in cmd_lower or "document" in cmd_lower:
            filename = "Notes.docx"
            content = clipboard if clipboard else f"Notes created for {self.identity.user_name}."
            steps.append({
                "tool": "create_word_document",
                "args": {"filename": filename, "content": content},
                "description": f"Create Word document '{filename}'"
            })

        # File Downloads
        elif "download" in cmd_lower:
            url_match = re.search(r'https?://[^\s]+', user_command)
            url = url_match.group(0) if url_match else "https://example.com"
            steps.append({"tool": "download_file", "args": {"url": url}, "description": f"Download file from {url}"})

        # Visual & Camera Perception
        elif any(w in cmd_lower for w in ["see me", "look at me", "can you see", "camera", "my face", "watch me", "how do i look"]):
            steps.append({
                "tool": "inspect_camera_snapshot",
                "args": {"purpose": "user_observation"},
                "description": "Observe Aswin through desktop camera snapshot"
            })

        # Self-Reflection & Memory Queries
        elif any(w in cmd_lower for w in ["what did you learn", "reflection", "mistakes", "learning status"]):
            steps.append({"tool": "get_current_time", "args": {}, "description": "Generate self-reflection report"})

        # Conversational Chit-Chat (No tool needed)
        elif self.is_conversational(user_command):
            return []

        # Default Fallback Acknowledgment
        else:
            steps.append({"tool": "get_current_time", "args": {}, "description": f"Process command for {self.identity.user_name}"})

        return steps

    def is_conversational(self, prompt: str) -> bool:
        """Check if user prompt is conversational chit-chat rather than an OS action."""
        p_lower = prompt.lower().strip()
        chat_triggers = [
            "hello", "hi", "hey", "how are you", "what's up", "who are you",
            "talk to me", "tell me a joke", "tell me something", "what do you think",
            "how's your day", "thanks", "thank you", "good morning", "good evening",
            "how do you feel", "are you there", "yo"
        ]
        return any(p_lower.startswith(t) or p_lower == t for t in chat_triggers)

    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Generate a frank, natural, direct conversational response for Aswin.
        """
        p_lower = prompt.lower().strip()
        name = self.identity.user_name

        if any(w in p_lower for w in ["hello", "hi", "hey", "yo"]):
            return f"Hey {name}! I'm right here with you on your desktop. What are we tackling today?"
        elif "how are you" in p_lower or "how's your day" in p_lower:
            return f"Running smooth and sharp, {name}. Zero cloud dependencies, watching over your PC. How's everything on your end?"
        elif "who are you" in p_lower:
            return f"I'm your private, sovereign assistant, {name}. Built exclusively for your machine. I see what you're working on, learn from mistakes, and keep everything 100% offline."
        elif "thank" in p_lower:
            return f"Always got your back, {name}. What's next?"
        elif "what do you think" in p_lower:
            return f"Honestly, {name}, keeping things local and disciplined is the smartest move. Let's get straight to work."
        else:
            return f"Got it, {name}. I'm listening—tell me what you need or give me the command."
