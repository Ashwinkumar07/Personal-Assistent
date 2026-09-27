"""
==============================================================================
User Identity & Personal Profile Management
==============================================================================
Manages user-specific preferences, identity verification, working habits,
and personalized contextual greetings for Aswin.
100% Private, Local, and Offline.
==============================================================================
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from core.config import PROJECT_ROOT, settings
from core.logger import logger

DEFAULT_PROFILE: Dict[str, Any] = {
    "user_name": "Aswin",
    "title": "Master",
    "preferred_greeting": "Hey Aswin",
    "tone": "concise, proactive, technical, and reliable",
    "primary_workspaces": [
        str(Path.home() / "OneDrive" / "Desktop"),
        str(Path.home() / "OneDrive" / "Documents"),
        str(Path.home() / "Downloads")
    ],
    "default_browser": "chrome",
    "favorite_apps": ["code", "chrome", "notepad", "powershell"],
    "privacy_mode": "STRICT_LOCAL",
    "auto_reflect_on_mistakes": True,
    "last_active": None,
    "created_at": datetime.now().isoformat()
}

class UserIdentity:
    """Manages the private profile and identity of the owner (Aswin)."""

    def __init__(self, profile_path: Optional[Path] = None):
        self.profile_path = profile_path or (PROJECT_ROOT / "data" / "user_profile.json")
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        self.profile: Dict[str, Any] = self._load_profile()

    def _load_profile(self) -> Dict[str, Any]:
        """Load profile from disk or initialize default."""
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {**DEFAULT_PROFILE, **data}
            except Exception as e:
                logger.error(f"[IDENTITY] Failed to read profile: {e}. Using defaults.")
        
        # Save default profile
        self._save_profile(DEFAULT_PROFILE)
        return DEFAULT_PROFILE.copy()

    def _save_profile(self, data: Dict[str, Any]) -> None:
        """Persist profile to disk."""
        try:
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"[IDENTITY] Failed to save profile: {e}")

    @property
    def user_name(self) -> str:
        return self.profile.get("user_name", "Aswin")

    @property
    def display_name(self) -> str:
        """Returns the user's preferred honorific/title (e.g., 'Sir') or their name."""
        return self.profile.get("preferred_title") or self.profile.get("user_name", "Aswin")

    def set_preferred_title(self, title: str) -> None:
        """Set how the assistant should address the user (e.g. 'Sir', 'Boss', 'Aswin')."""
        clean_title = title.strip().title()
        self.update_preference("preferred_title", clean_title)
        logger.info(f"[IDENTITY] Preferred user title updated to: '{clean_title}'")

    def update_preference(self, key: str, value: Any) -> None:
        """Update a specific user preference."""
        self.profile[key] = value
        self.profile["updated_at"] = datetime.now().isoformat()
        self._save_profile(self.profile)
        logger.info(f"[IDENTITY] Updated preference: '{key}' = '{value}'")

    def get_greeting(self, active_app: Optional[str] = None) -> str:
        """Generate a contextual, personalized greeting based on time of day and active task."""
        now = datetime.now()
        hour = now.hour
        
        if 5 <= hour < 12:
            time_greet = "Good morning"
        elif 12 <= hour < 17:
            time_greet = "Good afternoon"
        elif 17 <= hour < 22:
            time_greet = "Good evening"
        else:
            time_greet = "Working late"

        context_str = f" I see you're in {active_app}." if active_app else ""
        return f"{time_greet}, {self.user_name}!{context_str} Your desktop assistant is online and ready."

    def get_system_prompt_identity(self) -> str:
        """System prompt snippet asserting local ownership and personality."""
        return (
            f"You are a 100% private, sovereign desktop assistant built exclusively for {self.user_name}. "
            f"You never transmit data externally. Your tone is {self.profile['tone']}. "
            f"You operate with precision on Windows 11, learn from past mistakes, and adapt to {self.user_name}'s daily workflow."
        )
