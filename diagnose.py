"""
System & Dependency Diagnostic Script for Personal Assistant
"""
import sys
import os
from pathlib import Path

print("=" * 60)
print("  PERSONAL ASSISTANT SYSTEM DIAGNOSTIC")
print("=" * 60)
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"Current Directory: {os.getcwd()}")
print("-" * 60)

modules_to_test = [
    ("yaml", "pyyaml"),
    ("pydantic", "pydantic"),
    ("psutil", "psutil"),
    ("sounddevice", "sounddevice"),
    ("numpy", "numpy"),
    ("faster_whisper", "faster-whisper"),
    ("pyttsx3", "pyttsx3"),
    ("pystray", "pystray"),
    ("PIL", "Pillow"),
    ("keyboard", "keyboard"),
    ("cv2", "opencv-python")
]

missing = []

for mod_name, pkg_name in modules_to_test:
    try:
        __import__(mod_name)
        print(f"  [OK] {pkg_name} ({mod_name})")
    except ImportError as e:
        print(f"  [MISSING] {pkg_name} ({mod_name}) -> Error: {e}")
        missing.append(pkg_name)

print("-" * 60)

if missing:
    print(f"\n[!] Missing {len(missing)} package(s): {', '.join(missing)}")
    print("To install all missing packages, run:")
    print(f"  pip install {' '.join(missing)}")
else:
    print("\n[ALL GREEN] All required modules are installed and operational!")

print("=" * 60)
