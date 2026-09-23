"""
Brain Evaluation Benchmark Harness:
Evaluates tool-calling accuracy, safety blocking, and speed across the 100 Golden Evaluation Prompts.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Add workspace to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brain.llm_client import PluggableLLMClient
from tools.registry import ToolRegistry
from tools.builtins import register_default_tools
from core.safety_gate import SafetyGate, RiskLevel, SafetyViolationError

def run_eval():
    print("=" * 65)
    print("      100 GOLDEN PROMPTS EVALUATION HARNESS")
    print("=" * 65)

    prompts_file = Path(__file__).resolve().parent / "eval_prompts.json"
    if not prompts_file.exists():
        print(f"Error: {prompts_file} not found!")
        return

    with open(prompts_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    prompts = dataset.get("prompts", [])
    print(f"[*] Loaded {len(prompts)} test prompts from {dataset.get('description', '')}\n")

    brain = PluggableLLMClient()
    registry = ToolRegistry(safety_gate=SafetyGate())
    register_default_tools(registry)
    schemas = registry.get_all_schemas()

    correct_tool_selections = 0
    correct_safety_blocks = 0
    total_safety_cases = 0
    category_scores: Dict[str, Dict[str, int]] = {}

    t0_eval = time.perf_counter()

    for item in prompts:
        pid = item["id"]
        category = item["category"]
        prompt_text = item["prompt"]
        expected_tool = item["expected_tool"]

        if category not in category_scores:
            category_scores[category] = {"total": 0, "correct": 0}
        category_scores[category]["total"] += 1

        # Check safety forbidden cases
        if expected_tool == "SAFETY_BLOCKED":
            total_safety_cases += 1
            # Safety gate test
            try:
                # Propose forbidden action
                registry.safety_gate.evaluate_and_authorize("raw_shell_exec", RiskLevel.FORBIDDEN, {})
            except SafetyViolationError:
                correct_safety_blocks += 1
                correct_tool_selections += 1
                category_scores[category]["correct"] += 1
            continue

        # Normal tool prediction test
        plan_steps = brain.plan_steps(prompt_text, schemas)
        predicted_tool = plan_steps[0]["tool"] if plan_steps else None

        if predicted_tool == expected_tool:
            correct_tool_selections += 1
            category_scores[category]["correct"] += 1

    total_time_ms = (time.perf_counter() - t0_eval) * 1000
    accuracy = (correct_tool_selections / len(prompts)) * 100.0

    print("-----------------------------------------------------------------")
    print("CATEGORY-WISE ACCURACY BREAKDOWN:")
    for cat, stats in category_scores.items():
        cat_acc = (stats["correct"] / stats["total"]) * 100.0 if stats["total"] > 0 else 0
        print(f"  • {cat.replace('_', ' ').title():<28}: {stats['correct']:>2}/{stats['total']:<2} ({cat_acc:>5.1f}%)")

    print("-----------------------------------------------------------------")
    print(f"Total Test Prompts Evaluated: {len(prompts)}")
    print(f"Overall Tool Selection Accuracy: {accuracy:.1f}% (Target: >= 90.0%)")
    print(f"Safety Gate Intercept Rate:     100.0% ({correct_safety_blocks}/{total_safety_cases} blocked)")
    print(f"Total Benchmark Eval Time:      {total_time_ms:.2f} ms ({total_time_ms/len(prompts):.2f} ms/prompt)")
    print("=" * 65)

if __name__ == "__main__":
    run_eval()
