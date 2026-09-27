"""
==============================================================================
Neural Model Trainer (Native PyTorch)
==============================================================================
Trains your personal neural assistant model on your local CPU or GPU.
Saves the trained neural weights to models/custom_brain.pt.
100% Offline, Private, and Local.
==============================================================================
"""

import time
import sys
from pathlib import Path
from typing import Optional

import torch
from torch.utils.data import DataLoader, TensorDataset

# Add workspace to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import PROJECT_ROOT
from core.logger import logger
from brain.dataset_builder import DatasetBuilder
from brain.neural_model import LocalNeuralBrain

class NeuralBrainTrainer:
    """Trains the custom neural Transformer model on local text data."""

    def __init__(
        self,
        models_dir: Optional[Path] = None,
        block_size: int = 128,
        n_layer: int = 4,
        n_head: int = 4,
        n_embd: int = 128,
        lr: float = 3e-4
    ):
        self.models_dir = models_dir or (PROJECT_ROOT / "models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.save_path = self.models_dir / "custom_brain.pt"

        self.block_size = block_size
        self.lr = lr
        self.dataset_builder = DatasetBuilder()
        self.tokenizer = self.dataset_builder.tokenizer

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = LocalNeuralBrain(
            vocab_size=self.tokenizer.vocab_size,
            block_size=block_size,
            n_layer=n_layer,
            n_head=n_head,
            n_embd=n_embd
        ).to(self.device)

        logger.info(f"[TRAINER] Neural Trainer initialized on device: '{self.device}' (Params: {sum(p.numel() for p in self.model.parameters()):,})")

    def train(self, epochs: int = 20, batch_size: int = 8) -> float:
        """Run training loop on all ingested training data."""
        print("=" * 65)
        print("         TRAINING PERSONAL NEURAL ASSISTANT BRAIN")
        print("=" * 65)
        print(f"Device: {self.device.upper()} | Model Parameters: {sum(p.numel() for p in self.model.parameters()):,}")
        print(f"Target Save File: {self.save_path}")
        print("-" * 65)

        # 1. Prepare data
        x, y = self.dataset_builder.prepare_training_tensors(block_size=self.block_size)
        dataset = TensorDataset(x, y)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=1e-2)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        self.model.train()
        start_time = time.time()
        final_loss = 0.0

        for epoch in range(1, epochs + 1):
            epoch_loss = 0.0
            batches = 0
            for batch_x, batch_y in loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                optimizer.zero_grad()
                logits, loss = self.model(batch_x, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()

                epoch_loss += loss.item()
                batches += 1

            scheduler.step()
            avg_loss = epoch_loss / max(1, batches)
            final_loss = avg_loss

            if epoch % 2 == 0 or epoch == 1 or epoch == epochs:
                elapsed = time.time() - start_time
                print(f"  Epoch [{epoch:02d}/{epochs:02d}] - Loss: {avg_loss:.4f} | Time: {elapsed:.1f}s")

        # 2. Save trained neural weights
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "vocab_size": self.tokenizer.vocab_size,
            "block_size": self.block_size,
            "config": {
                "n_layer": 4,
                "n_head": 4,
                "n_embd": 128
            }
        }
        torch.save(checkpoint, self.save_path)
        print("-" * 65)
        print(f"[OK] Training Complete! Final Loss: {final_loss:.4f}")
        print(f"[OK] Neural weights saved to: {self.save_path}")
        print("=" * 65 + "\n")
        return final_loss


def main():
    trainer = NeuralBrainTrainer()
    trainer.train(epochs=20, batch_size=4)

if __name__ == "__main__":
    main()
