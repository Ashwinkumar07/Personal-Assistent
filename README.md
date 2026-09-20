# Fully Local Autonomous Desktop Assistant for Windows 11

A fully private, voice-driven, local personal assistant engineered for Windows 11 on the **HP EliteBook 830 G7** (Intel i7-10610U, 32 GB RAM, CPU-only).

---

## 🌟 Key Capabilities

- 🎙️ **Zero-Latency Voice Pipeline**: Local int8 `faster-whisper` STT and streaming `Piper` TTS.
- 🧠 **Local Tool-Calling Brain**: Quantized Qwen2.5/Qwen3 (1.5B–4B) fine-tuned for structured tool calls.
- 🛡️ **Multi-Tier Safety Gate**: Risk-tiered execution (`Read`, `Write`, `Destructive`, `Forbidden`), Recycle Bin file routing, automatic pre-edit backups, and `<1s` Global Kill Switch.
- ⚡ **Asynchronous Concurrency**: SQLite job queue running tasks in the background without freezing voice interaction.
- 👁️ **Screen Perception**: Windows UI Automation control tree inspection & local OCR (`RapidOCR`).
- 🧠 **3-Tier Persistent Memory**: Episodic (conversations), Semantic (facts & preferences), and Procedural (learned macros) with CPU vector search (`MiniLM`).
- 🔒 **100% Offline & Private**: Zero data sent to cloud, no subscriptions, no accounts.

---

## 📂 Project Architecture

```
Personal Assistant/
├── config/
│   └── settings.yaml          # Central unified configuration
├── core/
│   ├── config.py              # Pydantic schema validation for settings
│   ├── logger.py              # Latency tracker and audit logger
│   ├── orchestrator.py        # Core state machine loop
│   ├── safety_gate.py         # Multi-tier risk evaluator & backup manager
│   ├── job_queue.py           # SQLite-backed background task manager
│   └── kill_switch.py         # Global hotkey emergency stop listener (<1s)
├── voice/
│   ├── audio_io.py            # Sounddevice non-blocking audio capture
│   ├── vad.py                 # Silero VAD speech segmentation
│   ├── stt.py                 # faster-whisper int8 transcriber
│   └── tts.py                 # Piper sentence-streaming speech synthesizer
├── brain/
│   ├── llm_client.py          # llama.cpp / Ollama local GGUF client
│   └── prompt_templates.py    # Structured tool-calling prompts & system schemas
├── tools/
│   ├── base.py                # Pydantic tool definitions & risk metadata
│   ├── registry.py            # Dynamic tool loader
│   └── builtins/              # Safe native OS and system tools
├── awareness/
│   ├── uia_scanner.py         # Windows UI Automation accessibility tree reader
│   └── ocr_scanner.py         # Local RapidOCR screen reader
├── memory/
│   ├── database.py            # SQLite schema for episodic, semantic, procedural memory
│   └── vector_store.py        # all-MiniLM-L6-v2 vector index
├── adapters/                  # App connectors (Office COM, Playwright, CLIs)
├── ui/
│   └── tray_app.py            # pystray system tray & notification control center
├── benchmarks/                # Hardware latency & evaluation benchmark test scripts
├── tests/                     # Unit and integration test suites
├── scripts/
│   └── sync_repo.py           # Auto-commit and push script for GitHub
└── main.py                    # Main bootstrap entry point
```

---

## 🚀 Quickstart & Setup

### 1. Create Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run Benchmark Suite
```powershell
python benchmarks/bench_voice.py
```

### 4. Automated Git Sync
```powershell
python scripts/sync_repo.py "Completed Module X"
```
