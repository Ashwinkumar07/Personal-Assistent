"""
Master Bootstrap & Entry Point:
Fully Local, Free, and Independent Desktop Assistant for Windows 11.
"""

import sys
import time
import signal
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
from core.proactive_coach import ProactiveCoach
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
from ui.tray_app import SystemTrayApp
from voice.tts import TextToSpeech
from voice.continuous_listener import ContinuousVoiceListener

def main():
    # 1. Initialize User Identity & Reflection Engine
    identity = UserIdentity()
    reflection_engine = SelfReflectionEngine()

    print("=" * 68)
    print(f"      {settings.app.name.upper()} v{settings.app.version}")
    print(f"      Owner: {identity.user_name} | 100% Private, Local Windows 11")
    print("=" * 68)

    # 2. Initialize Safety & Core Infrastructure
    kill_switch = KillSwitch()
    safety_gate = SafetyGate()
    registry = ToolRegistry(safety_gate=safety_gate)

    # 3. Register Builtin Tools & App Adapters
    register_default_tools(registry)
    registry.register(BrowserAdapter())
    registry.register(DownloaderAdapter())
    registry.register(GetPhoneStatusTool())
    registry.register(CreateWordDocumentTool())
    registry.register(GitStatusTool())
    registry.register(OpenVSCodeTool())

    logger.info(f"Loaded {len(registry.list_tools())} total capabilities and tools.")

    # 4. Start Background Job Workers & Awareness Observers
    job_queue = JobQueue()
    worker_pool = WorkerPool(queue=job_queue, registry=registry, kill_switch=kill_switch)
    worker_pool.start()

    activity_observer = ActivityObserver(poll_interval_sec=10.0)
    activity_observer.start()

    memory_mgr = MemoryManager()
    coach = ProactiveCoach(job_queue=job_queue)
    orchestrator = Orchestrator(
        registry=registry,
        safety_gate=safety_gate,
        kill_switch=kill_switch,
        reflection_engine=reflection_engine
    )
    brain = AdaptiveLocalBrain(user_identity=identity, reflection_engine=reflection_engine)

    # 5. Initialize Text-to-Speech engine
    tts = TextToSpeech()

    # 6. Start Hands-Free Continuous Voice Listener (Graceful Fallback)
    voice_listener = None
    voice_active = False
    try:
        def handle_voice_command(spoken_text: str) -> str:
            """Handle voice commands spoken by Aswin."""
            active_win = activity_observer.get_current_active_window() if hasattr(activity_observer, "get_current_active_window") else ""
            context = {"active_window": active_win, "user": identity.user_name}
            
            if brain.is_conversational(spoken_text):
                return brain.generate_response(spoken_text, context=active_win)
            
            steps = brain.plan_steps(spoken_text, registry.get_all_schemas(), context=context)
            if not steps:
                return brain.generate_response(spoken_text, context=active_win)
            
            # Execute steps
            res = orchestrator.execute_plan(goal=spoken_text, steps=steps)
            return f"Done! Executed {len(steps)} step(s) for you, {identity.user_name}."

        voice_listener = ContinuousVoiceListener(on_command_callback=handle_voice_command, tts_engine=tts)
        voice_listener.start()
        voice_active = True
    except Exception as e:
        logger.warning(f"[VOICE] Continuous voice listener could not start: {e}. Console input is active.")
        voice_active = False

    # 7. Launch System Tray Icon (Graceful Fallback)
    try:
        tray_app = SystemTrayApp(kill_switch=kill_switch, on_exit_callback=worker_pool.stop)
        tray_app.run_in_background()
    except Exception as e:
        logger.debug(f"[TRAY APP] Tray icon fallback: {e}")

    greeting_msg = identity.get_greeting()
    print(f"\n[✔] {greeting_msg}")
    if voice_active:
        print(f"[🎙️] Hands-Free Voice Listener is ACTIVE (Speak anytime into your mic).")
    else:
        print(f"[💬] Text Console Mode ACTIVE.")
    print(f"[!] Kill Switch Hotkey: '{settings.safety.kill_switch_hotkey}'")
    print("[!] Special Commands: 'reflection' (view learned rules), 'profile', or 'exit'.\n")

    # Speak initial greeting
    tts.speak(f"Hello {identity.user_name}! Your local personal assistant is online and ready.")

    def shutdown():
        goodbye_msg = f"Shutting down assistant. See you tomorrow, {identity.user_name}!"
        print(f"\n{goodbye_msg}")
        tts.speak(goodbye_msg)
        if voice_listener:
            voice_listener.stop()
        worker_pool.stop()
        activity_observer.stop()
        kill_switch.stop_listener()
        sys.exit(0)

    def interactive_confirmation(prompt_text: str) -> bool:
        """Strictly ask Aswin for confirmation before executing any action."""
        try:
            choice = input(f"🔒 [Confirm Action] {prompt_text} -> Proceed? [Y/n]: ").strip().lower()
            return choice in ("", "y", "yes")
        except (KeyboardInterrupt, EOFError):
            return False

    # Command loop (Interactive Desktop Assistant)
    try:
        while not kill_switch.is_triggered:
            try:
                user_cmd = input(f"{identity.user_name} > ").strip()
                if not user_cmd:
                    continue
                if user_cmd.lower() in ("exit", "quit"):
                    shutdown()

                # Special Command: Reflection Summary
                if user_cmd.lower() in ("reflection", "learned", "learning status"):
                    refl_text = reflection_engine.generate_daily_reflection()
                    print(f"\n[Reflection Engine] {refl_text}\n")
                    tts.speak("Here is the daily reflection summary of learned rules.")
                    continue

                # Special Command: View Profile
                if user_cmd.lower() in ("profile", "who am i", "my settings"):
                    prof_text = f"Name: {identity.user_name}, Tone: {identity.profile.get('tone')}, Workspaces: {identity.profile.get('primary_workspaces')}"
                    print(f"\n[User Profile] {prof_text}\n")
                    tts.speak(f"You are {identity.user_name}. Personal preferences loaded.")
                    continue

                # Contextual perception
                active_win = activity_observer.get_current_active_window() if hasattr(activity_observer, "get_current_active_window") else ""
                context = {"active_window": active_win, "user": identity.user_name}

                # 1. Check if conversational chit-chat
                if brain.is_conversational(user_cmd):
                    reply = brain.generate_response(user_cmd, context=active_win)
                    print(f"[Assistant] {reply}\n")
                    tts.speak(reply)
                    continue

                # 2. Decompose actionable command into steps
                steps = brain.plan_steps(user_cmd, registry.get_all_schemas(), context=context)
                
                if not steps:
                    reply = brain.generate_response(user_cmd, context=active_win)
                    print(f"[Assistant] {reply}\n")
                    tts.speak(reply)
                    continue

                print(f"[Plan Proposed] {len(steps)} step(s):")
                for i, s in enumerate(steps):
                    print(f"  [{i+1}] {s.get('description')} (Tool: {s.get('tool')})")

                # 3. Orchestrator executes steps strictly asking for confirmation
                result = orchestrator.execute_plan(
                    goal=user_cmd,
                    steps=steps,
                    confirm_callback=interactive_confirmation
                )
                print(f"[Assistant] Execution Result: {result.get('step_results')}\n")
                tts.speak(f"I have executed the task for you, {identity.user_name}.")

                # Check for completed background jobs
                coach.check_background_jobs_and_notify()

            except (KeyboardInterrupt, EOFError):
                shutdown()
    finally:
        shutdown()

if __name__ == "__main__":
    main()
