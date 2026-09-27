"""
==============================================================================
Neural Inference Engine
==============================================================================
Loads custom-trained PyTorch weights from models/custom_brain.pt and generates
fluid, learned text responses autoregressively.
100% Offline, Native PyTorch.
==============================================================================
"""

import sys
from pathlib import Path
from typing import Optional

import torch

# Add workspace to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import PROJECT_ROOT
from core.logger import logger
from brain.dataset_builder import SimpleByteTokenizer
from brain.neural_model import LocalNeuralBrain

class NeuralInferenceEngine:
    """Runs autoregressive text generation from custom trained neural weights."""

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or (PROJECT_ROOT / "models" / "custom_brain.pt")
        self.tokenizer = SimpleByteTokenizer()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model: Optional[LocalNeuralBrain] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load trained neural checkpoint if it exists."""
        if not self.model_path.exists():
            logger.debug(f"[INFERENCE] No custom neural checkpoint found at {self.model_path}.")
            return

        try:
            checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
            cfg = checkpoint.get("config", {"n_layer": 4, "n_head": 4, "n_embd": 128})
            
            self.model = LocalNeuralBrain(
                vocab_size=checkpoint.get("vocab_size", self.tokenizer.vocab_size),
                block_size=checkpoint.get("block_size", 128),
                n_layer=cfg.get("n_layer", 4),
                n_head=cfg.get("n_head", 4),
                n_embd=cfg.get("n_embd", 128)
            ).to(self.device)

            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.model.eval()
            logger.info(f"[INFERENCE] Custom neural model successfully loaded from {self.model_path}!")
        except Exception as e:
            logger.error(f"[INFERENCE] Failed loading neural model: {e}")
            self.model = None

    @property
    def is_available(self) -> bool:
        return self.model is not None

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 120,
        temperature: float = 0.7,
        top_k: int = 40
    ) -> str:
        """Generate response from trained neural model."""
        if not self.is_available:
            return ""

        input_tokens = self.tokenizer.encode(prompt, add_special_tokens=False)
        idx = torch.tensor([input_tokens], dtype=torch.long, device=self.device)
        
        with torch.no_grad():
            out_idx = self.model.generate(
                idx,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k
            )

        gen_tokens = out_idx[0].tolist()[len(input_tokens):]
        generated_text = self.tokenizer.decode(gen_tokens).strip()
        return generated_text
