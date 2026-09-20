#!/usr/bin/env python3
"""
Automated Git Synchronization Script for Personal Assistant.
Usage:
    python scripts/sync_repo.py "Commit message describing the completed module/task"
"""

import sys
import subprocess
from pathlib import Path

def run_cmd(cmd: list[str]) -> bool:
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return result.returncode == 0

def main():
    message = sys.argv[1] if len(sys.argv) > 1 else "Auto-sync: Progress update"
    
    print("=== [1/3] Staging modified files ===")
    if not run_cmd(["git", "add", "."]):
        print("Failed to stage files.")
        return

    print(f"=== [2/3] Committing with message: '{message}' ===")
    commit_res = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True)
    if commit_res.returncode != 0:
        if "nothing to commit" in commit_res.stdout or "nothing to commit" in commit_res.stderr:
            print("Working directory clean, nothing new to commit.")
        else:
            print(f"Commit error: {commit_res.stderr.strip()}")
            return
    else:
        print(commit_res.stdout.strip())

    print("=== [3/3] Pushing to remote (if configured) ===")
    remotes = subprocess.run(["git", "remote"], capture_output=True, text=True).stdout.strip()
    if remotes:
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip() or "main"
        if run_cmd(["git", "push", "origin", branch]):
            print("Successfully pushed changes to remote repository!")
        else:
            print("Push failed or remote not reachable. Local commits are preserved.")
    else:
        print("No Git remote configured yet. To connect to GitHub, run:")
        print("   git remote add origin <your-github-repo-url>")
        print("   git branch -M main")
        print("   git push -u origin main")

if __name__ == "__main__":
    main()
