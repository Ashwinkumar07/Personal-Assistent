import os
from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class AppConfig(BaseModel):
    name: str = "Local Desktop Assistant"
    version: str = "0.1.0"
    log_level: str = "INFO"
    log_dir: str = "logs"
    data_dir: str = "data"

class HardwareConfig(BaseModel):
    cpu_threads_total: int = 8
    cpu_threads_stt: int = 4
    cpu_threads_llm: int = 4
    cpu_threads_tts: int = 2
    max_ram_budget_mb: int = 10240

class VadConfig(BaseModel):
    enabled: bool = True
    threshold: float = 0.5
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 700

class SttConfig(BaseModel):
    model_size: str = "base.en"
    device: str = "cpu"
    compute_type: str = "int8"
    download_root: str = "models/whisper"
    beam_size: int = 1
    language: str = "en"

class TtsConfig(BaseModel):
    model_name: str = "en_US-lessac-medium"
    models_dir: str = "models/piper"
    sample_rate: int = 22050
    speaker_id: int = 0
    sentence_silence: float = 0.15

class VoiceConfig(BaseModel):
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration_ms: int = 30
    push_to_talk_key: str = "f8"
    vad: VadConfig = Field(default_factory=VadConfig)
    stt: SttConfig = Field(default_factory=SttConfig)
    tts: TtsConfig = Field(default_factory=TtsConfig)

class BrainConfig(BaseModel):
    backend: str = "llama_cpp"
    model_path: str = "models/llm/qwen2.5-3b-instruct-q4_k_m.gguf"
    context_size: int = 4096
    temperature: float = 0.2
    num_threads: int = 4
    max_tokens: int = 512

class SafetyConfig(BaseModel):
    run_as_admin: bool = False
    recycle_bin_deletes: bool = True
    backup_before_write: bool = True
    backup_dir: str = "data/backups"
    kill_switch_hotkey: str = "ctrl+shift+f12"
    sandbox_directories: List[str] = Field(default_factory=list)

class MemoryConfig(BaseModel):
    db_path: str = "data/memory.sqlite3"
    embedding_model: str = "all-MiniLM-L6-v2"
    auto_summarize_interval_hours: int = 6

class ConcurrencyConfig(BaseModel):
    max_workers: int = 3
    worker_priority: str = "BELOW_NORMAL_PRIORITY_CLASS"

class Settings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    brain: BrainConfig = Field(default_factory=BrainConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    concurrency: ConcurrencyConfig = Field(default_factory=ConcurrencyConfig)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Settings":
        if config_path is None:
            config_path = PROJECT_ROOT / "config" / "settings.yaml"
        
        if not config_path.exists():
            return cls()
        
        with open(config_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f) or {}
            
        return cls(**raw_data)

settings = Settings.load()
