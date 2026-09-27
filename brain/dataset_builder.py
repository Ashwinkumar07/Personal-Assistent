"""
==============================================================================
Dataset Builder & Tokenizer for Local Neural Model Training
==============================================================================
Collects raw text, books, dialogue pairs, SQLite memory logs, and documentation,
trains a subword BPE/Byte tokenizer, and produces PyTorch training tensors.
100% Offline, Native PyTorch & Python.
==============================================================================
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import torch
from core.config import PROJECT_ROOT
from core.logger import logger

class SimpleByteTokenizer:
    """
    Fast, zero-dependency UTF-8 Byte-level Tokenizer with special tokens.
    Guarantees zero unknown tokens (out-of-vocabulary) and handles any text.
    """
    def __init__(self):
        # 0: <PAD>, 1: <BOS>, 2: <EOS>, 3: <USER>, 4: <ASSISTANT>, 5: <SYS>
        self.special_tokens = {
            "<PAD>": 0,
            "<BOS>": 1,
            "<EOS>": 2,
            "<USER>": 3,
            "<ASSISTANT>": 4,
            "<SYS>": 5
        }
        self.special_ids = {v: k for k, v in self.special_tokens.items()}
        self.vocab_size = 256 + len(self.special_tokens)

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        byte_vals = list(text.encode("utf-8"))
        offset = len(self.special_tokens)
        token_ids = [b + offset for b in byte_vals]
        if add_special_tokens:
            return [self.special_tokens["<BOS>"]] + token_ids + [self.special_tokens["<EOS>"]]
        return token_ids

    def decode(self, token_ids: List[int]) -> str:
        offset = len(self.special_tokens)
        raw_bytes = bytearray()
        for t in token_ids:
            if t in self.special_ids:
                continue
            byte_val = t - offset
            if 0 <= byte_val <= 255:
                raw_bytes.append(byte_val)
        return raw_bytes.decode("utf-8", errors="replace")


class DatasetBuilder:
    """Collects and prepares training text from raw files and SQLite memory."""

    def __init__(self, data_dir: Optional[Path] = None, memory_db_path: Optional[Path] = None):
        self.data_dir = data_dir or (PROJECT_ROOT / "data" / "training_data")
        self.memory_db_path = memory_db_path or (PROJECT_ROOT / "data" / "memory.sqlite3")
        self.tokenizer = SimpleByteTokenizer()
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def collect_all_text(self) -> str:
        """Read all text from training files and SQLite database."""
        corpus = []

        # 1. Read files in data/training_data/
        for file_path in self.data_dir.glob("*.*"):
            if file_path.suffix.lower() in (".txt", ".md", ".jsonl"):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore").strip()
                    if content:
                        corpus.append(content)
                        logger.info(f"[DATASET] Ingested '{file_path.name}' ({len(content)} chars)")
                except Exception as e:
                    logger.error(f"[DATASET] Failed reading {file_path}: {e}")

        # 2. Extract SQLite memories (Facts, Rules, Dialogue)
        if self.memory_db_path.exists():
            try:
                conn = sqlite3.connect(self.memory_db_path)
                cursor = conn.cursor()
                
                # Semantic Facts
                cursor.execute("SELECT key, value FROM semantic_memory")
                for k, v in cursor.fetchall():
                    corpus.append(f"Fact about {k}: {v}")

                # Dialogue turns
                cursor.execute("SELECT role, content FROM episodic_memory ORDER BY id ASC")
                dialogues = cursor.fetchall()
                for role, content in dialogues:
                    corpus.append(f"{role.capitalize()}: {content}")

                conn.close()
                logger.info(f"[DATASET] Extracted facts and dialogue logs from SQLite memory.")
            except Exception as e:
                logger.debug(f"[DATASET] Memory extraction note: {e}")

        # 3. Add default seed knowledge if corpus is small
        if len(corpus) == 0 or sum(len(c) for c in corpus) < 100:
            seed_data = self._get_seed_knowledge()
            corpus.append(seed_data)
            seed_file = self.data_dir / "seed_knowledge.txt"
            seed_file.write_text(seed_data, encoding="utf-8")
            logger.info("[DATASET] Created default seed knowledge dataset.")

        full_text = "\n\n".join(corpus)
        logger.info(f"[DATASET] Total training corpus: {len(full_text):,} characters.")
        return full_text

    def prepare_training_tensors(self, block_size: int = 128) -> Tuple[torch.Tensor, torch.Tensor]:
        """Convert collected text into input (x) and target (y) PyTorch tensors."""
        text = self.collect_all_text()
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        
        if len(tokens) <= block_size:
            # Pad tokens if text is short
            tokens = tokens * (block_size // max(1, len(tokens)) + 2)

        data = torch.tensor(tokens, dtype=torch.long)
        num_blocks = (len(data) - 1) // block_size
        
        x_list = []
        y_list = []
        for i in range(num_blocks):
            start_idx = i * block_size
            x_list.append(data[start_idx : start_idx + block_size])
            y_list.append(data[start_idx + 1 : start_idx + block_size + 1])

        x = torch.stack(x_list)
        y = torch.stack(y_list)
        logger.info(f"[DATASET] Prepared {len(x)} sequence blocks (block_size={block_size}).")
        return x, y

    def _get_seed_knowledge(self) -> str:
        """Foundational conversational, coding, reasoning, and tool-use dataset."""
        return """
Assistant Identity & Knowledge:
Owner: Aswin (also addressed as Sir).
Platform: 100% Private, Local Desktop Assistant on Windows 11.
Capabilities: Answering questions, writing Python code, file management, checking system specs, launching apps, and remembering facts.

Conversation Examples:
User: Who is your creator?
Assistant: You are my creator, Sir! (Aswin). You designed and built me to be your private sovereign desktop assistant.

User: What is your primary purpose?
Assistant: My purpose is to assist you with programming, computer tasks, learning, and productivity while keeping 100% of your data private on your PC.

User: What can you do?
Assistant: I can launch apps, check system telemetry, write notes, search information, manage files, and remember your personal preferences.

User: How do you learn?
Assistant: I learn in two ways: first, through my real-time memory and self-reflection engine; second, through training on your personal notes, code, and documents.

Programming Knowledge:
Python is a high-level, interpreted programming language known for readability and clean syntax.
Functions in Python are defined using the 'def' keyword.
Classes in Python support object-oriented programming with inheritance and encapsulation.
In PyTorch, neural networks inherit from torch.nn.Module and implement the forward method.
"""
