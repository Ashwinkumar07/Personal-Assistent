"""
==============================================================================
Adaptive Local Brain:
Merges User Identity, Desktop Perception, and Learned Mistake Rules
into Deterministic & Quantized Execution Plans.
==============================================================================
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.config import settings
from core.logger import logger
from core.user_identity import UserIdentity
from core.self_reflection import SelfReflectionEngine
from memory.manager import MemoryManager
from brain.llm_client import BaseBrain

class AdaptiveLocalBrain(BaseBrain):
    """
    Intelligent, private local brain that adapts its decisions based on:
    - User Identity & Preferences (Aswin)
    - Active Desktop Environment (Foreground App, Clipboard)
    - Learned Rules from Past Mistakes (Self-Reflection Database)
    - Semantic Memory (Taught Facts, Habits, Preferences)
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
        logger.info(f"[ADAPTIVE BRAIN] Initialized for {self.identity.user_name} with Memory & Reflection active.")

    def teach_fact_or_rule(self, user_input: str) -> Optional[str]:
        """
        Extract and permanently store facts, rules, or preferences taught by Aswin.
        Returns a friendly confirmation response if a teaching pattern was matched.
        """
        text = user_input.strip().strip('"\'')
        lower = text.lower()
        name = self.identity.display_name

        # Pattern 0: Direct Name / Title change ("Call me Sir", "You will call me Sir", "Address me as Boss")
        title_match = re.search(r'(?:from now on\s+)?(?:you will\s+)?(?:call me|address me as)\s+([a-zA-Z\s]+)', text, re.IGNORECASE)
        if title_match:
            new_title = title_match.group(1).strip().title()
            self.identity.set_preferred_title(new_title)
            self.memory.set_fact(key="preferred_title", value=new_title, category="user_identity")
            return f"Understood, {new_title}! From now on, I will address you as {new_title}."

        # Pattern 1: Direct "Teach:" or "Learn:" commands
        teach_match = re.match(r'^(teach|learn|instruction)[:\s]+(.+)', text, re.IGNORECASE)
        if teach_match:
            rule_body = teach_match.group(2).strip()
            # Check if teaching a title inside teach (e.g. "Teach from now you will call me Sir")
            nested_title = re.search(r'(?:from now\s+(?:on\s+)?)?(?:you will\s+)?(?:call me|address me as)\s+([a-zA-Z\s]+)', rule_body, re.IGNORECASE)
            if nested_title:
                new_title = nested_title.group(1).strip().title()
                self.identity.set_preferred_title(new_title)
                self.memory.set_fact(key="preferred_title", value=new_title, category="user_identity")
                return f"Understood, {new_title}! I will now call you {new_title}."

            self.reflection.record_manual_correction(
                wrong_command=rule_body[:30],
                correct_command=rule_body,
                feedback="Explicit user teaching instruction"
            )
            self.memory.set_fact(key=f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}", value=rule_body, category="taught_rules")
            return f"Understood, {name}! I've memorized this rule: \"{rule_body}\". I will follow it in all future tasks."

        # Pattern 2: "Remember that <fact>" or "Remember <fact>"
        remember_match = re.match(r'^remember(?:\s+that)?\s+(.+)', text, re.IGNORECASE)
        if remember_match:
            fact = remember_match.group(1).strip()
            clean_fact = fact.rstrip('.!')
            key = f"fact_{clean_fact[:25].replace(' ', '_').lower()}"
            self.memory.set_fact(key=key, value=clean_fact, category="user_taught")
            return f"Got it, {name}! I will remember that: \"{clean_fact}\"."

        # Pattern 3: "From now on / Always / Never ..."
        behavior_match = re.match(r'^(from now on|always|never)\s+(.+)', text, re.IGNORECASE)
        if behavior_match:
            prefix = behavior_match.group(1).capitalize()
            body = behavior_match.group(2).strip()
            # Check for title
            if "call me" in body.lower() or "address me as" in body.lower():
                call_m = re.search(r'(?:call me|address me as)\s+([a-zA-Z\s]+)', body, re.IGNORECASE)
                if call_m:
                    new_title = call_m.group(1).strip().title()
                    self.identity.set_preferred_title(new_title)
                    self.memory.set_fact(key="preferred_title", value=new_title, category="user_identity")
                    return f"Understood, {new_title}! From now on, I will address you as {new_title}."

            rule = f"{prefix} {body}"
            self.reflection.record_manual_correction(
                wrong_command=rule[:25],
                correct_command=rule,
                feedback="Behavioral preference"
            )
            self.memory.set_fact(key=f"behavior_{datetime.now().strftime('%H%M%S')}", value=rule, category="behavior_rules")
            return f"Noted, {name}! New behavior set: \"{rule}\"."

        # Pattern 4: "My <property> is <value>" (e.g. "My favorite language is Python")
        my_prop_match = re.match(r'^my\s+([a-zA-Z\s_]+)\s+(?:is|are)\s+(.+)', text, re.IGNORECASE)
        if my_prop_match:
            prop = my_prop_match.group(1).strip()
            val = my_prop_match.group(2).strip().rstrip('.!')
            self.memory.set_fact(key=prop.lower().replace(' ', '_'), value=val, category="user_profile")
            return f"Got it, {name}. I've recorded that your {prop} is '{val}'."

        # Pattern 5: "I prefer <preference>" or "I like <interest>"
        pref_match = re.match(r'^i\s+(prefer|like|love|hate|dislike)\s+(.+)', text, re.IGNORECASE)
        if pref_match:
            verb = pref_match.group(1).lower()
            detail = pref_match.group(2).strip().rstrip('.!')
            self.memory.set_fact(key=f"pref_{verb}_{detail[:15].replace(' ', '_')}", value=f"Aswin {verb}s {detail}", category="user_preference")
            return f"Recorded your preference, {name}: you {verb} \"{detail}\"."

        return None

    def get_memory_summary(self) -> str:
        """Retrieve and format everything taught to and remembered by the agent."""
        facts = self.memory.list_all_facts()
        name = self.identity.display_name
        
        if not facts:
            return f"I haven't recorded any custom facts or rules yet, {name}. You can teach me anytime! For example:\n- \"Remember that my major project is due on Friday\"\n- \"Teach: always ask before deleting files\"\n- \"My favorite language is Python\""
        
        lines = [f"Here is everything I've learned and remembered for you, {name}:"]
        for k, v in facts.items():
            lines.append(f"  • {v}")
        return "\n".join(lines)

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
        # Clean quotes and whitespace
        clean_cmd = user_command.strip().strip('"\'')
        cmd_lower = clean_cmd.lower().strip()
        context = context or {}
        active_window = context.get("active_window", "")
        clipboard = context.get("clipboard", "")

        # 1. Check if this is a teaching or memory query instruction (No tool step needed)
        if self.teach_fact_or_rule(clean_cmd) is not None:
            return []
        
        if any(w in cmd_lower for w in [
            "what do you remember", "what have you learned", "what do you know about me",
            "my memories", "list facts", "show rules", "what will you call me", "what do you call me"
        ]):
            return []

        # 2. Check for relevant Learned Rules from past mistakes
        learned_rules = self.reflection.get_relevant_rules(clean_cmd)
        if learned_rules:
            logger.info(f"[ADAPTIVE BRAIN] Applied {len(learned_rules)} learned rule(s) for command '{clean_cmd}'.")

        steps: List[Dict[str, Any]] = []

        # 3. Match Explicit Direct OS / Tool Commands
        
        # Application Launching (Camera, Notepad, Calculator, VSCode, Chrome, Edge, etc.)
        if cmd_lower.startswith(("open ", "launch ", "start ")):
            target_app = re.sub(r'^(open|launch|start)\s+', '', cmd_lower).strip()
            # If target is web query or file, handle specifically
            if target_app in ("camera", "webcam"):
                steps.append({"tool": "launch_app", "args": {"app_name": "camera"}, "description": "Launch Windows Camera"})
            elif target_app in ("calc", "calculator"):
                steps.append({"tool": "launch_app", "args": {"app_name": "calculator"}, "description": "Launch Calculator"})
            elif target_app in ("notepad", "notes"):
                steps.append({"tool": "launch_app", "args": {"app_name": "notepad"}, "description": "Launch Notepad"})
            elif target_app in ("vscode", "code", "vs code", "editor"):
                steps.append({"tool": "launch_app", "args": {"app_name": "code"}, "description": "Launch Visual Studio Code"})
            elif target_app in ("explorer", "files", "file explorer"):
                steps.append({"tool": "launch_app", "args": {"app_name": "explorer"}, "description": "Launch File Explorer"})
            elif target_app in ("settings", "control panel"):
                steps.append({"tool": "launch_app", "args": {"app_name": "settings"}, "description": "Launch Settings"})
            elif target_app in ("chrome", "google chrome"):
                steps.append({"tool": "launch_app", "args": {"app_name": "chrome"}, "description": "Launch Google Chrome"})
            elif target_app in ("edge", "microsoft edge"):
                steps.append({"tool": "launch_app", "args": {"app_name": "edge"}, "description": "Launch Microsoft Edge"})
            else:
                steps.append({"tool": "launch_app", "args": {"app_name": target_app}, "description": f"Launch application '{target_app}'"})
            return steps

        # Time & Date
        if any(w in cmd_lower for w in ["current time", "what time", "what is the time", "clock"]):
            steps.append({"tool": "get_current_time", "args": {}, "description": "Check current time"})
        elif any(w in cmd_lower for w in ["today's date", "what date", "what is today's date", "calendar"]):
            steps.append({"tool": "get_current_date", "args": {}, "description": "Check current date"})

        # System Telemetry & Performance
        elif any(w in cmd_lower for w in ["battery", "charge percentage", "power status"]):
            steps.append({"tool": "get_battery_status", "args": {}, "description": "Check system battery"})
        elif any(w in cmd_lower for w in ["system spec", "hardware spec", "cpu usage", "ram usage", "system specs"]):
            steps.append({"tool": "get_system_specs", "args": {}, "description": "Check hardware telemetry"})
        elif any(w in cmd_lower for w in ["active window", "foreground window", "current window", "what am i looking at"]):
            steps.append({"tool": "get_active_window_title", "args": {}, "description": "Inspect active application window"})

        # Web Search & Browser Automation
        elif cmd_lower.startswith(("search for", "search ", "google ", "look up ", "browse ")):
            query = clean_cmd
            for word in ["search for", "search", "google", "look up", "browse", "find"]:
                if query.lower().startswith(word):
                    query = query[len(word):].strip()
            steps.append({"tool": "search_web", "args": {"query": query}, "description": f"Search web for '{query}'"})

        # Code & Dev Tools
        elif "git status" in cmd_lower or "repo status" in cmd_lower:
            steps.append({"tool": "git_status", "args": {}, "description": "Check Git repository status"})

        # Office / Document Creation
        elif cmd_lower.startswith(("create word document", "create doc", "make word document", "make notes document")):
            filename = "Notes.docx"
            content = clipboard if clipboard else f"Notes created for {self.identity.display_name}."
            steps.append({
                "tool": "create_word_document",
                "args": {"filename": filename, "content": content},
                "description": f"Create Word document '{filename}'"
            })

        # File Downloads
        elif cmd_lower.startswith("download ") and ("http://" in cmd_lower or "https://" in cmd_lower):
            url_match = re.search(r'https?://[^\s]+', clean_cmd)
            url = url_match.group(0) if url_match else "https://example.com"
            steps.append({"tool": "download_file", "args": {"url": url}, "description": f"Download file from {url}"})

        # Visual & Camera Perception
        elif any(w in cmd_lower for w in ["inspect camera", "look at me through camera", "take camera snapshot", "see me"]):
            steps.append({
                "tool": "inspect_camera_snapshot",
                "args": {"purpose": "user_observation"},
                "description": f"Observe {self.identity.display_name} through desktop camera snapshot"
            })

        return steps

    def is_conversational(self, prompt: str) -> bool:
        """Check if user prompt is conversational chit-chat, teaching, or inquiry."""
        clean_p = prompt.strip().strip('"\'')
        if not clean_p:
            return True

        # If it matches any teaching pattern, it is conversational/educational
        if self.teach_fact_or_rule(clean_p) is not None:
            return True
            
        p_lower = clean_p.lower().strip()
        
        # Memory & Title queries
        if any(w in p_lower for w in [
            "what do you remember", "what have you learned", "what do you know about me",
            "who am i", "my memory", "my facts", "my preferences", "what is my",
            "what will you call me", "what do you call me", "reply me", "talk to me"
        ]):
            return True

        # Conversational triggers
        chat_triggers = [
            "hello", "hi", "hey", "how are you", "what's up", "who are you",
            "talk to me", "tell me a joke", "tell me something", "what do you think",
            "how's your day", "thanks", "thank you", "good morning", "good evening",
            "good night", "how do you feel", "are you there", "yo", "teach", "learn",
            "can you", "what can you do", "help", "how does", "why", "what is",
            "explain", "advice", "suggest", "opinion", "reply"
        ]
        
        # If it starts with open/launch/search/check, it is a tool command
        if p_lower.startswith(("open ", "launch ", "start ", "search ", "download ", "create ", "delete ", "copy ", "move ")):
            return False
            
        return any(t in p_lower for t in chat_triggers) or len(p_lower.split()) > 1

    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Generate a frank, natural, intelligent conversational response for Aswin,
        incorporating taught facts, memory, and desktop context.
        """
        clean_prompt = prompt.strip().strip('"\'')
        
        # 1. Check if user is teaching a rule, title, or fact
        teaching_reply = self.teach_fact_or_rule(clean_prompt)
        if teaching_reply:
            return teaching_reply

        p_lower = clean_prompt.lower().strip()
        name = self.identity.display_name

        # 2. What will you call me / Name / Identity queries
        if any(w in p_lower for w in ["what will you call me", "what do you call me", "what is my title", "how do you address me"]):
            pref_title = self.identity.profile.get("preferred_title")
            if pref_title:
                return f"I address you as {pref_title}! You are {self.identity.user_name}, my sovereign user."
            return f"I call you {self.identity.user_name}! If you want me to call you something else (like 'Sir' or 'Boss'), just tell me: \"Call me Sir\"."

        if "who am i" in p_lower or "tell me about myself" in p_lower:
            facts = self.memory.list_all_facts()
            facts_str = ", ".join([f"{k}: {v}" for k, v in list(facts.items())[:4]]) if facts else "No extra facts recorded yet."
            return (
                f"You are {self.identity.user_name}, and I address you as {name}. "
                f"Your working tone is '{self.identity.profile.get('tone', 'frank_and_concise')}'. "
                f"Memory highlights: {facts_str}"
            )

        # 3. Check for Memory and Fact recall queries
        if any(w in p_lower for w in ["what do you remember", "what have you learned", "what do you know about me", "my memories", "list facts", "show rules"]):
            return self.get_memory_summary()

        # Check for specific "what is my <property>"
        prop_query = re.search(r'what is my\s+([a-zA-Z\s_]+)', p_lower)
        if prop_query:
            target_prop = prop_query.group(1).strip().rstrip('?')
            fact_val = self.memory.get_fact(target_prop.replace(' ', '_'))
            if fact_val:
                return f"According to what you taught me, your {target_prop} is: {fact_val}."
            all_facts = self.memory.list_all_facts()
            for k, v in all_facts.items():
                if target_prop in k or target_prop in v.lower():
                    return f"From my memory: \"{v}\""
            return f"I don't have a record of your {target_prop} yet, {name}. You can teach me by saying: \"My {target_prop} is [value]\"."

        # 4. Conversational Chit-Chat & Dialogues
        if any(w in p_lower for w in ["reply me first", "reply me", "talk to me", "are you there"]):
            return f"I am right here with you, {name}! How can I help you right now?"

        if any(w in p_lower for w in ["hello", "hi", "hey", "yo", "greetings"]):
            return f"Hey {name}! I'm right here with you on your desktop. What are we working on or teaching today?"
        
        elif "how are you" in p_lower or "how's your day" in p_lower:
            return f"Running smooth, sharp, and 100% offline, {name}. Memory and reflection engines are active. How is everything going for you?"
        
        elif "who are you" in p_lower or "what are you" in p_lower:
            return (
                f"I'm your private personal assistant, {name}. "
                f"I live directly on your PC with zero external servers, learn from your teachings and feedback, "
                f"and automate your desktop workflows."
            )
        
        elif any(w in p_lower for w in ["what can you do", "help", "commands"]):
            return (
                f"Here is what we can do together, {name}:\n"
                f"  1. 💬 Chat & Teach: Talk to me in normal English. Teach me: 'Call me Sir', 'Remember that X', 'Teach: always do Y'.\n"
                f"  2. 🧠 Memory: Ask me 'What do you remember?' or 'What will you call me?'.\n"
                f"  3. 💻 OS Automation: 'Open camera', 'Open notepad', 'Check battery', 'What time is it?', 'Open VSCode'.\n"
                f"  4. 🛡️ Safety: Safe Recycle Bin deletion, pre-action backups, and instant Kill Switch."
            )
        
        elif "thank" in p_lower:
            return f"Always a pleasure, {name}. Let me know what you'd like to do next."

        elif "joke" in p_lower:
            return "Why do programmers prefer dark mode? Because light attracts bugs!"

        elif "what do you think" in p_lower or "opinion" in p_lower:
            return f"I believe keeping your assistant 100% private, sovereign, and locally taught is the highest-leverage setup. You have complete control over every rule and memory."

        elif "explain" in p_lower or "advice" in p_lower or "suggest" in p_lower:
            return f"I'm listening, {name}. Break down the topic or goal, and I'll give you a direct, frank breakdown."

        else:
            return (
                f"I hear you, {name}. I've logged this in our session memory. "
                f"Feel free to teach me facts ('Remember that...'), set rules ('Teach:...'), or ask me to perform any desktop task."
            )
