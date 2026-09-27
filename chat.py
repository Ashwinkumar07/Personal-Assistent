"""
==============================================================================
Personal Assistant - Interactive Chat & Teaching Console
==============================================================================
Fast, distraction-free conversational and teaching interface.
Talk to your assistant in normal English, teach it facts, set rules,
and execute desktop actions without background microphone interference.
==============================================================================
"""

import sys
import os
from pathlib import Path

# Add workspace to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import settings
from core.logger import logger
from core.safety_gate import SafetyGate
from core.kill_switch import KillSwitch
from core.job_queue import JobQueue
from core.worker import WorkerPool
from core.orchestrator import Orchestrator
from core.user_identity import UserIdentity
from core.self_reflection import SelfReflectionEngine
from tools.registry import ToolRegistry
from tools.builtins import register_default_tools
from adapters.browser_adapter import BrowserAdapter
from adapters.downloader import DownloaderAdapter
from adapters.phone_adapter import GetPhoneStatusTool
from adapters.office_adapter import CreateWordDocumentTool
from adapters.code_adapter import GitStatusTool, OpenVSCodeTool
from memory.manager import MemoryManager
from awareness.active_app import ActivityObserver
from brain.adaptive_brain import AdaptiveLocalBrain
from voice.tts import TextToSpeech

def main():
    identity = UserIdentity()
    reflection_engine = SelfReflectionEngine()
    memory_mgr = MemoryManager()
    
    kill_switch = KillSwitch()
    safety_gate = SafetyGate()
    registry = ToolRegistry(safety_gate=safety_gate)

    register_default_tools(registry)
    registry.register(BrowserAdapter())
    registry.register(DownloaderAdapter())
    registry.register(GetPhoneStatusTool())
    registry.register(CreateWordDocumentTool())
    registry.register(GitStatusTool())
    registry.register(OpenVSCodeTool())

    job_queue = JobQueue()
    worker_pool = WorkerPool(queue=job_queue, registry=registry, kill_switch=kill_switch)
    worker_pool.start()

    activity_observer = ActivityObserver(poll_interval_sec=10.0)
    activity_observer.start()

    orchestrator = Orchestrator(
        registry=registry,
        safety_gate=safety_gate,
        kill_switch=kill_switch,
        reflection_engine=reflection_engine
    )

    brain = AdaptiveLocalBrain(
        user_identity=identity,
        reflection_engine=reflection_engine,
        memory_manager=memory_mgr
    )

    tts = TextToSpeech()
    speak_enabled = True

    print("\n" + "=" * 68)
    print("        PERSONAL ASSISTANT - TEACH & CHAT CONSOLE")
    print(f"        Owner: {identity.user_name} | 100% Private, Local AI")
    print("=" * 68)
    print("[💡] What you can do:")
    print("  • Teach facts:    \"Remember that my college project is due Friday\"")
    print("  • Teach rules:    \"Teach: always check git branch before pushing\"")
    print("  • Teach profile:  \"My favorite programming language is Python\"")
    print("  • View memory:    Type 'memory' or \"What do you remember?\"")
    print("  • Perform tasks:  \"Check battery\", \"What time is it?\", \"Open VSCode\"")
    print("  • Special cmds:   'memory', 'rules', 'profile', 'voice on/off', 'exit'")
    print("=" * 68 + "\n")

    greeting = identity.get_greeting()
    print(f"[Assistant] {greeting} How can I help or what would you like to teach me today?\n")

    def shutdown():
        print(f"\n[Assistant] Goodbye {identity.user_name}! All learned memories saved locally.\n")
        worker_pool.stop()
        activity_observer.stop()
        kill_switch.stop_listener()
        sys.exit(0)

    def interactive_confirmation(prompt_text: str) -> bool:
        try:
            choice = input(f"🔒 [Confirm Action] {prompt_text} -> Proceed? [Y/n]: ").strip().lower()
            return choice in ("", "y", "yes")
        except (KeyboardInterrupt, EOFError):
            return False

    while not kill_switch.is_triggered:
        try:
            user_cmd = input(f"{identity.user_name} > ").strip()
            if not user_cmd:
                continue

            if user_cmd.lower() in ("exit", "quit", "q", "bye"):
                shutdown()

            if user_cmd.lower() == "clear":
                os.system('cls' if os.name == 'nt' else 'clear')
                continue

            if user_cmd.lower() in ("voice on", "tts on", "sound on"):
                speak_enabled = True
                print("[Assistant] Spoken audio output enabled.\n")
                continue

            if user_cmd.lower() in ("voice off", "tts off", "sound off", "mute"):
                speak_enabled = False
                print("[Assistant] Spoken audio output muted (Text only).\n")
                continue

            # Special Command: Memory
            if user_cmd.lower() in ("memory", "facts", "what do you remember", "memories"):
                mem_text = brain.get_memory_summary()
                print(f"\n[Memory Store]\n{mem_text}\n")
                continue

            # Special Command: Reflection & Learned Rules
            if user_cmd.lower() in ("reflection", "learned", "rules", "learning status"):
                refl_text = reflection_engine.generate_daily_reflection()
                print(f"\n[Reflection Engine]\n{refl_text}\n")
                continue

            # Special Command: Profile
            if user_cmd.lower() in ("profile", "who am i", "my settings"):
                prof_text = f"Name: {identity.user_name}\nTone: {identity.profile.get('tone')}\nWorkspaces: {identity.profile.get('primary_workspaces')}"
                print(f"\n[User Profile]\n{prof_text}\n")
                continue

            # Context
            active_win = activity_observer.get_current_active_window() if hasattr(activity_observer, "get_current_active_window") else ""
            context = {"active_window": active_win, "user": identity.user_name}

            # Record in episodic dialogue
            memory_mgr.record_dialogue(role="user", content=user_cmd)

            # 1. Conversational & Teaching Handler
            if brain.is_conversational(user_cmd):
                reply = brain.generate_response(user_cmd, context=active_win)
                print(f"\n[Assistant] {reply}\n")
                memory_mgr.record_dialogue(role="assistant", content=reply)
                if speak_enabled:
                    tts.speak(reply)
                continue

            # 2. Planning & Tool Execution
            steps = brain.plan_steps(user_cmd, registry.get_all_schemas(), context=context)
            if not steps:
                reply = brain.generate_response(user_cmd, context=active_win)
                print(f"\n[Assistant] {reply}\n")
                memory_mgr.record_dialogue(role="assistant", content=reply)
                if speak_enabled:
                    tts.speak(reply)
                continue

            print(f"\n[Plan Proposed] {len(steps)} step(s):")
            for i, s in enumerate(steps):
                print(f"  [{i+1}] {s.get('description')} (Tool: {s.get('tool')})")

            result = orchestrator.execute_plan(
                goal=user_cmd,
                steps=steps,
                confirm_callback=interactive_confirmation
            )
            print(f"[Assistant] Execution Result: {result.get('step_results')}\n")
            if speak_enabled:
                tts.speak(f"Executed {len(steps)} step(s) for you, {identity.user_name}.")

        except (KeyboardInterrupt, EOFError):
            shutdown()

if __name__ == "__main__":
    main()
