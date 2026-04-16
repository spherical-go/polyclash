"""NeuralNet wrapper for spherical Go.

Bridges the AlphaZero NeuralNet interface with the GraphHRM model.
Handles state-to-tensor conversion, device management, and checkpointing.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional, Tuple

import numpy as np

from polyclash.ai.core.neural import NeuralNet
from polyclash.ai.polyclash.state import PolyclashState
from polyclash.ai.polyclash.topology import (
    area_weight,
    coords_3d,
    edge_index,
    node_type,
)

_TORCH_OK = True
try:
    import torch
    from torch import nn
    from torch.nn import functional as F

    from polyclash.ai.nn.model import GraphHRMModel
except Exception as e:
    print(f"WARNING: Failed to import torch dependencies: {e}")
    _TORCH_OK = False
    torch = None  # type: ignore

log = logging.getLogger(__name__)


class NNetWrapper(NeuralNet):
    """Spherical Go NNet wrapper — device-agnostic, graph-aware."""

    def __init__(self, game):
        self.game = game
        self.action_size_val = game.action_size()
        self.device = None
        self.torch_model: Optional[nn.Module] = None

        # Precompute graph tensors (shared across all forward passes)
        self._edge_index_np = edge_index
        self._node_type_np = node_type
        self._coords_np = coords_3d.astype(np.float32)
        self._area_weight_np = area_weight.astype(np.float32)

        if _TORCH_OK:
            self.torch_model = GraphHRMModel()

            force_cpu = os.environ.get("FORCE_CPU_SELFPLAY", "0") == "1"
            if force_cpu:
                self.device = torch.device("cpu")
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")

            self.torch_model.to(self.device)

            # Precompute graph tensors on device
            self._edge_index_t = torch.tensor(
                self._edge_index_np, dtype=torch.int64, device=self.device
            )
            self._node_type_t = torch.tensor(
                self._node_type_np, dtype=torch.int64, device=self.device
            )
            self._coords_t = torch.tensor(
                self._coords_np, dtype=torch.float32, device=self.device
            )
            self._area_weight_t = torch.tensor(
                self._area_weight_np, dtype=torch.float32, device=self.device
            )

            log.info(f"NeuralNet on device: {self.device}")

    def _state_to_stones(self, state: PolyclashState) -> np.ndarray:
        """Extract stones array from a PolyclashState."""
        return np.array(state.stones, dtype=np.int64)

    def train(self, examples: List[Tuple], args=None):
        if self.torch_model is None or len(examples) == 0:
            return

        device = self.device
        model = self.torch_model
        model.train()

        lr = args.get("lr", 1e-3) if args else 1e-3
        weight_decay = args.get("weight_decay", 0.0) if args else 0.0
        epochs = args.get("pl_max_epochs", 5) if args else 5
        batch_size = args.get("batch_size", 32) if args else 32

        optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

        # Detect whether examples carry auxiliary targets (5-tuple vs 3-tuple).
        # During transition, history may mix both formats; use aux only if ALL have it.
        has_aux = all(len(ex) == 5 for ex in examples)

        log.info(
            f"Training: {len(examples)} examples, {epochs} epochs, "
            f"batch={batch_size}, lr={lr}, aux={has_aux}"
        )

        for epoch in range(epochs):
            total_loss: float = 0.0
            num_batches = 0

            for start in range(0, len(examples), batch_size):
                chunk = examples[start : start + batch_size]

                scores: Optional[Tuple] = None
                owns: Optional[Tuple] = None
                if has_aux:
                    states, pis, vs, scores, owns = list(zip(*chunk))
                else:
                    states, pis, vs = list(zip(*chunk))

                # Convert states to stones tensors
                stones_list = [self._state_to_stones(s) for s in states]
                stones_t = torch.tensor(
                    np.array(stones_list), dtype=torch.long, device=device
                )
                target_pis = torch.tensor(
                    np.array(pis), dtype=torch.float32, device=device
                )
                target_vs = torch.tensor(
                    np.array(vs), dtype=torch.float32, device=device
                )

                out = model(
                    stones_t,
                    self._edge_index_t,
                    self._node_type_t,
                    self._coords_t,
                    self._area_weight_t,
                    return_aux=has_aux,
                )

                if has_aux:
                    logits, pred_v, pred_score, pred_own = out
                else:
                    logits, pred_v = out

                # Policy loss
                log_probs = F.log_softmax(logits, dim=1)
                loss_pi = -torch.sum(target_pis * log_probs) / stones_t.size(0)

                # Value loss
                loss_v = torch.mean((target_vs - pred_v.view(-1)) ** 2)

                loss = loss_pi + loss_v

                # Auxiliary losses
                if has_aux:
                    target_scores = torch.tensor(
                        np.array(scores), dtype=torch.float32, device=device
                    )
                    target_owns = torch.tensor(
                        np.array(owns), dtype=torch.float32, device=device
                    )

                    # Score loss (MSE)
                    loss_score = torch.mean((target_scores - pred_score.view(-1)) ** 2)

                    # Ownership loss (BCE with logits, area-weighted)
                    # target_owns in [-1, 1], convert to [0, 1] for BCE
                    own_target_01 = (target_owns + 1.0) * 0.5
                    loss_own = F.binary_cross_entropy_with_logits(
                        pred_own,
                        own_target_01,
                        weight=self._area_weight_t.unsqueeze(0),
                        reduction="mean",
                    )

                    loss = loss + 0.5 * loss_score + 0.5 * loss_own

                optim.zero_grad()
                loss.backward()
                optim.step()

                total_loss += loss.item()
                num_batches += 1

            avg_loss = total_loss / max(num_batches, 1)
            log.info(f"  Epoch {epoch + 1}/{epochs} avg_loss={avg_loss:.4f}")

    def predict(self, board: PolyclashState):
        if self.torch_model is not None and self.device is not None:
            self.torch_model.eval()
            with torch.no_grad():
                stones = self._state_to_stones(board)
                stones_t = torch.tensor(
                    stones, dtype=torch.long, device=self.device
                ).unsqueeze(0)

                logits, v = self.torch_model(
                    stones_t,
                    self._edge_index_t,
                    self._node_type_t,
                    self._coords_t,
                    self._area_weight_t,
                )
                logits = logits[0]
                v = v[0, 0].item()

                # Mask invalid moves
                valids = self.game.valid_moves(board, 1).astype(np.float64)
                logits_np = logits.detach().cpu().numpy().astype(np.float64)
                max_logit = np.max(logits_np)
                exp_logits = np.exp(logits_np - max_logit) * valids
                if exp_logits.sum() <= 0:
                    if valids.sum() > 0:
                        pi = valids / valids.sum()
                    else:
                        pi = np.ones_like(valids) / len(valids)
                else:
                    pi = exp_logits / exp_logits.sum()
                return pi, float(v)

        # Dummy path
        valids = self.game.valid_moves(board, 1)
        if np.sum(valids) == 0:
            pi = np.ones(self.action_size_val, dtype=np.float64) / float(
                self.action_size_val
            )
        else:
            pi = valids.astype(np.float64)
            pi /= np.sum(pi)
        return pi, 0.0

    def save_checkpoint(self, folder="checkpoint", filename="checkpoint.pkl"):
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
        if self.torch_model is not None and _TORCH_OK:
            torch.save({"state_dict": self.torch_model.state_dict()}, filepath)

            # Also save safetensors version alongside .pkl
            st_path = os.path.splitext(filepath)[0] + ".safetensors"
            try:
                from safetensors.torch import save_file

                save_file(self.torch_model.state_dict(), st_path)
                log.info("Saved safetensors checkpoint: %s", st_path)
            except Exception as e:
                log.warning("Failed to save safetensors: %r", e)

    def push_to_hub(
        self,
        repo_id: str = "mingli/hrm-polyclash",
        proxy: Optional[str] = None,
        commit_message: str = "Update model",
    ):
        """Push current weights to HuggingFace Hub as safetensors."""
        if self.torch_model is None or not _TORCH_OK:
            log.warning("Torch not available; skipping Hub push.")
            return

        import json
        import tempfile

        from huggingface_hub import HfApi
        from safetensors.torch import save_file

        proxy = proxy or os.environ.get("HF_PROXY")
        if proxy:
            saved = {
                k: os.environ.get(k) for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")
            }
            os.environ["HTTP_PROXY"] = proxy
            os.environ["HTTPS_PROXY"] = proxy
            os.environ["ALL_PROXY"] = proxy
            log.info("Using proxy %s for Hub push", proxy)
        else:
            saved = None

        try:
            api = HfApi()
            api.create_repo(repo_id=repo_id, exist_ok=True, repo_type="model")

            with tempfile.TemporaryDirectory() as tmpdir:
                st_path = os.path.join(tmpdir, "model.safetensors")
                save_file(self.torch_model.state_dict(), st_path)

                config = {
                    "hidden": 192,
                    "graph_layers": 2,
                    "hrm_layers": 2,
                    "num_heads": 8,
                    "h_cycles": 1,
                    "l_cycles": 2,
                }
                config_path = os.path.join(tmpdir, "config.json")
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2)

                for local, remote in [
                    (st_path, "model.safetensors"),
                    (config_path, "config.json"),
                ]:
                    api.upload_file(
                        path_or_fileobj=local,
                        path_in_repo=remote,
                        repo_id=repo_id,
                        commit_message=commit_message,
                    )

            log.info("Pushed weights to HuggingFace Hub: %s", repo_id)
        finally:
            if saved is not None:
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

    def load_from_hub(
        self,
        repo_id: str = "mingli/hrm-polyclash",
        filename: str = "model.safetensors",
        proxy: Optional[str] = None,
    ):
        """Download and load weights from a HuggingFace Hub repository.

        Args:
            proxy: SOCKS5/HTTP proxy URL, e.g. ``socks5h://127.0.0.1:7070``.
                   Also read from env ``HF_PROXY`` if not given.
        """
        if self.torch_model is None or not _TORCH_OK:
            log.warning("Torch not available; skipping Hub download.")
            return
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file

        proxy = proxy or os.environ.get("HF_PROXY")
        if proxy:
            saved = {
                k: os.environ.get(k) for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")
            }
            os.environ["HTTP_PROXY"] = proxy
            os.environ["HTTPS_PROXY"] = proxy
            os.environ["ALL_PROXY"] = proxy
            log.info("Using proxy %s for Hub download", proxy)
        else:
            saved = None

        try:
            local_path = hf_hub_download(repo_id=repo_id, filename=filename)
        finally:
            if saved is not None:
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

        state = load_file(local_path, device="cpu")
        self.torch_model.load_state_dict(state, strict=False)
        self.torch_model.to(self.device)
        log.info("Loaded weights from HuggingFace Hub: %s/%s", repo_id, filename)

    def push_pool_member(
        self,
        repo_id: str,
        member_name: str,
        proxy: Optional[str] = None,
    ):
        """Upload current weights as a pool member to HF Hub."""
        if self.torch_model is None or not _TORCH_OK:
            return
        import tempfile

        from huggingface_hub import HfApi
        from safetensors.torch import save_file

        proxy = proxy or os.environ.get("HF_PROXY")
        if proxy:
            saved = {
                k: os.environ.get(k) for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")
            }
            os.environ["HTTP_PROXY"] = proxy
            os.environ["HTTPS_PROXY"] = proxy
            os.environ["ALL_PROXY"] = proxy
        else:
            saved = None

        try:
            api = HfApi()
            with tempfile.TemporaryDirectory() as tmpdir:
                st_path = os.path.join(tmpdir, f"{member_name}.safetensors")
                save_file(self.torch_model.state_dict(), st_path)
                api.upload_file(
                    path_or_fileobj=st_path,
                    path_in_repo=f"opponents/{member_name}.safetensors",
                    repo_id=repo_id,
                    commit_message=f"Add pool member {member_name}",
                )
            log.info("Pushed pool member %s to Hub", member_name)
        finally:
            if saved is not None:
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

    def delete_pool_member(
        self,
        repo_id: str,
        member_name: str,
        proxy: Optional[str] = None,
    ):
        """Delete a pool member from HF Hub."""
        from huggingface_hub import HfApi

        proxy = proxy or os.environ.get("HF_PROXY")
        if proxy:
            saved = {
                k: os.environ.get(k) for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")
            }
            os.environ["HTTP_PROXY"] = proxy
            os.environ["HTTPS_PROXY"] = proxy
            os.environ["ALL_PROXY"] = proxy
        else:
            saved = None

        try:
            api = HfApi()
            api.delete_file(
                path_in_repo=f"opponents/{member_name}.safetensors",
                repo_id=repo_id,
                commit_message=f"Evict pool member {member_name}",
            )
            log.info("Deleted pool member %s from Hub", member_name)
        except Exception as e:
            log.warning("Failed to delete pool member %s: %r", member_name, e)
        finally:
            if saved is not None:
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

    def load_pool_member(
        self,
        repo_id: str,
        member_name: str,
        proxy: Optional[str] = None,
    ):
        """Download and load a pool member's weights from HF Hub."""
        self.load_from_hub(
            repo_id=repo_id,
            filename=f"opponents/{member_name}.safetensors",
            proxy=proxy,
        )

    def state_dict(self):
        """Return model state dict (or None if no torch model)."""
        if self.torch_model is not None:
            return self.torch_model.state_dict()
        return None

    def load_state_dict(self, state_dict):
        """Load model state dict (strict=False for backward compat with old checkpoints)."""
        if self.torch_model is not None and state_dict is not None:
            self.torch_model.load_state_dict(state_dict, strict=False)

    def load_checkpoint(self, folder="checkpoint", filename="checkpoint.pkl"):
        filepath = os.path.join(folder, filename)

        # Prefer safetensors if available
        st_path = os.path.splitext(filepath)[0] + ".safetensors"
        if os.path.exists(st_path) and self.torch_model is not None and _TORCH_OK:
            try:
                from safetensors.torch import load_file

                state = load_file(st_path, device="cpu")
                self.torch_model.load_state_dict(state, strict=False)
                log.info("Loaded safetensors checkpoint: %s", st_path)
                return
            except Exception as e:
                log.warning("safetensors load failed, falling back to pkl: %r", e)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"No model in path {filepath}")
        if self.torch_model is not None and _TORCH_OK:
            try:
                checkpoint = torch.load(filepath, map_location="cpu", weights_only=True)
            except Exception as e:
                log.error("Failed to load checkpoint: %r", e)
                return
            state = checkpoint.get("state_dict", checkpoint)
            try:
                self.torch_model.load_state_dict(state)
            except Exception:
                self.torch_model.load_state_dict(state, strict=False)
