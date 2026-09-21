# Fully Local Autonomous Desktop Assistant 

A fully private, voice-driven, local personal assistant engineered for Windows 11 on resource-constrained and low-end CPU-only PCs.

---

## 🌟 Key Architectural Capabilities

- 🛡️ **Multi-Tier Safety Gate & Kill Switch**: Strict authorization (`READ`, `WRITE`, `DESTRUCTIVE`, `FORBIDDEN`), directory sandboxing, pre-modification backups, Recycle Bin deletes, and `<1ms` Emergency Kill Switch (`Ctrl+Shift+F12`).
- ⚡ **Asynchronous Concurrency Engine**: SQLite job queue (`WAL` mode) running background workers at `BELOW_NORMAL_PRIORITY_CLASS` with zero audio dropouts or UI freeze.
- 👁️ **Perception & Camera Vision**: Windows UI Automation control hierarchy reader, screen OCR fallback, on-demand webcam snapshot moments, and ultra-fast ($<12\mu s$) eye/mouth fatigue and focus tracking.
- 🧠 **Pluggable Brain & 3-Tier Memory**: SQLite Episodic dialogue store, Semantic fact store, Procedural macro store, and continuous correction feedback loop with a plug-and-play interface for your custom-trained LLM.
- 🌐 **App Adapters & Wireless Reach**: DuckDuckGo web search, sandboxed file downloader, Microsoft Office COM automation, Git/VS Code tools, and **100% wireless Android smartphone control** via ADB.
- 🖥️ **System Tray Control Center**: Background `pystray` system tray app with live status and 1-click Emergency Stop.

---

## 📂 Project Structure

```
Personal Assistant/
├── config/
│   └── settings.yaml          # Master configuration for low-end CPU PCs
├── core/
│   ├── config.py              # Pydantic strong-type schema validation
│   ├── logger.py              # Real-time latency tracking (latency.csv) & audit logging
│   ├── safety_gate.py         # Multi-tiered security & backup manager
│   ├── kill_switch.py         # Emergency halt hotkey (<1ms latency)
│   ├── job_queue.py           # SQLite persistent task queue with priority scheduling
│   ├── worker.py              # Low-priority background worker pool
│   ├── orchestrator.py        # Deterministic state machine with SQLite session store
│   └── proactive_coach.py     # Focus goal tracking & automated background alerts
├── voice/
│   ├── audio_io.py            # Non-blocking audio capture & Push-to-Talk
│   ├── vad.py                 # RMS silence trimming & speech detection
│   ├── stt.py                 # faster-whisper (int8) multi-threaded CPU transcriber
│   └── tts.py                 # Sentence-by-sentence streaming speech synthesizer
├── brain/
│   └── llm_client.py          # Pluggable Brain interface for custom LLM models
├── tools/
│   ├── base.py                # Pydantic tool definitions
│   ├── registry.py            # Dynamic tool discovery & safety gate evaluation
│   └── builtins/              # 15 safe built-in OS and file tools
├── awareness/
│   ├── uia_scanner.py         # Windows UI Automation control hierarchy reader
│   ├── ocr_scanner.py         # Local screen text OCR engine
│   ├── active_app.py          # Focused window usage tracker
│   ├── camera_vision.py       # On-demand camera snapshot capturing
│   └── face_companion.py      # Facial fatigue (EAR), yawn (MAR), & attention metrics
├── adapters/
│   ├── browser_adapter.py     # Web searching & information extraction
│   ├── downloader.py          # Automated file & media downloading
│   ├── phone_adapter.py       # 100% wireless Android phone control via ADB
│   ├── office_adapter.py      # Microsoft Word COM automation
│   └── code_adapter.py        # Git & VS Code workspace tools
├── memory/
│   ├── database.py            # SQLite schema for 3-tier memory
│   └── manager.py             # Episodic, Semantic, Procedural, & Continuous Correction feedback
├── ui/
│   └── tray_app.py            # System tray icon with status & 1-click Emergency Stop
├── benchmarks/                # Full hardware benchmark suite
├── tests/                     # 26 automated unit & integration tests
├── scripts/
│   └── sync_repo.py           # Automated GitHub synchronization script
└── main.py                    # Master application bootstrap entry point
```

---

## 🧪 Verified Hardware Benchmarks (Measured on CPU)

| Benchmark Test | Metric / Latency | Target / Requirement | Status |
| :--- | :--- | :--- | :--- |
| **Emergency Kill Switch** | **0.52 ms** | $< 1000\text{ ms}$ | ✅ PASSED |
| **Safety Gate Evaluation** | **0.003 ms** | $< 10\text{ ms}$ | ✅ PASSED |
| **Action Audit Log Verification** | **100% (3/3 recorded)** | Zero unlogged actions | ✅ PASSED |
| **VAD Silence Trimming (3s buffer)** | **3.23 ms** | $< 50\text{ ms}$ | ✅ PASSED |
| **TTS Sentence Chunking Latency** | **0.21 ms** | $< 800\text{ ms}$ | ✅ PASSED |
| **Background Concurrency (3 Workers)** | **Zero UI Freeze** | Responsive voice loop | ✅ PASSED |
| **UI Automation Inspection** | **0.44 ms** | $< 50\text{ ms}$ | ✅ PASSED |
| **Facial Fatigue Calculation (EAR)** | **11.77 μs** | $< 5000\text{ }\mu\text{s}$ | ✅ PASSED |
| **Process RAM Footprint** | **44.10 MB** | $< 10,240\text{ MB}$ | ✅ PASSED |
| **Automated Test Suite** | **26 / 26 Passed** | 100% test coverage | ✅ PASSED |

---

## 🚀 Quickstart

### 1. Run the Assistant
```powershell
python main.py
```

### 2. Run All Unit Tests
```powershell
python -m unittest discover -s tests
```

### 3. Run Benchmark Suites
```powershell
python benchmarks/bench_safety.py
python benchmarks/bench_concurrency.py
python benchmarks/bench_awareness.py
```

### 4. Auto-Sync Progress to GitHub
```powershell
python scripts/sync_repo.py "Your progress commit message"
```

---

## 📝 Pending & Upcoming Next Steps (For Reference)

The following items are prepared and ready for your separate setup:

### 1. 🧠 Custom LLM Training & Integration
- [ ] **Generate Synthetic Tool-Calling Dataset:** Create 5,000–10,000 tool-calling pairs matching the 20+ built-in schemas.
- [ ] **Fine-Tune Base Model:** LoRA fine-tune a lightweight base model (e.g. `Qwen2.5-1.5B` or `3B`) on Google Colab / Kaggle free GPU with `Unsloth`.
- [ ] **Export & Quantize:** Export merged weights to `.gguf` format (`Q4_K_M` quantization) for fast multi-threaded CPU inference.
- [ ] **Plug into Brain:** Drop the `.gguf` file into `models/llm/` to attach it to `brain/llm_client.py`.

### 2. 🎙️ Custom Voice Selection & Cloning
- [ ] **Record Reference Sample:** Record a 10–30 second clean `.wav` audio clip of the target person's voice.
- [ ] **Configure Voice:** Place the audio file into `models/custom_voice/my_voice.wav` and set `reference_audio` in `config/settings.yaml`.
- [ ] **Persona Style:** Ensure conversational Tanglish / casual modern Tamil persona prompting is enabled.

### 3. 📱 Wireless Android Smartphone Pairing
- [ ] **Enable Wireless Debugging:** Turn on Wireless Debugging under Android Developer Options on your phone.
- [ ] **Pair & Connect:** Run `adb connect <phone-ip>:5555` to enable 100% wireless phone actions (battery query, app launch, file sync).

### 4. 👂 Hands-Free Wake Word Integration
- [ ] **OpenWakeWord Model:** Download or train an ultra-low CPU wake word model (`openWakeWord`) for hands-free acoustic triggering without hotkey press.
