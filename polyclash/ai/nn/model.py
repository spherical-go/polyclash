"""Graph-HRM model for spherical Go.

Architecture:
  Node features → Graph encoder (message passing) → prepend CLS token → HRM backbone → policy + value heads

Input:  stones (B, 302) with values in {-1, 0, 1}
Output: (policy_logits (B, 303), value (B, 1))
"""

from __future__ import annotations

import torch
from huggingface_hub import PyTorchModelHubMixin
from torch import nn

from polyclash.ai.polyclash.topology import NUM_POINTS

from .graph_layers import GraphEncoder
from .hrm import (
    HierarchicalReasoningModel,
    HierarchicalReasoningModelCarry,
    HierarchicalReasoningModelConfig,
)


class GraphHRMModel(
    nn.Module,
    PyTorchModelHubMixin,
    repo_url="https://huggingface.co/mingli/hrm-polyclash",
    license="mit",
    tags=["spherical-go", "alphazero", "hrm", "graph-neural-network"],
):
    """Spherical Go model: GraphEncoder + HRM backbone.

    The 302-point board is treated as a graph of 302 node-tokens plus 1 CLS token.
    The graph encoder captures local topology, then HRM backbone does global reasoning.
    """

    def __init__(
        self,
        hidden: int = 192,
        graph_layers: int = 2,
        hrm_layers: int = 2,
        num_heads: int = 8,
        h_cycles: int = 1,
        l_cycles: int = 2,
    ) -> None:
        super().__init__()
        self.hidden = hidden
        self.num_points = NUM_POINTS

        # Node embeddings
        self.stone_emb = nn.Embedding(3, hidden)  # {-1, 0, +1} -> {0, 1, 2}
        self.type_emb = nn.Embedding(6, hidden)  # node_type in {1, 2, 3, 5}
        self.coord_proj = nn.Sequential(
            nn.Linear(3, hidden),
            nn.GELU(),
            nn.Linear(hidden, hidden),
        )

        # Learnable CLS token
        self.cls_token = nn.Parameter(torch.zeros(1, 1, hidden))

        # Graph encoder (local message passing)
        self.graph_encoder = GraphEncoder(hidden, num_layers=graph_layers)

        # HRM backbone (global reasoning)
        # Use pos_emb_type="none" since we handle positions via graph structure
        cfg = HierarchicalReasoningModelConfig(
            beginning_tokens=1,  # CLS token
            height=1,  # Not used (no 2D structure)
            width=NUM_POINTS,  # Treat as 1D sequence of 302 tokens
            n_layers=hrm_layers,
            hidden_size=hidden,
            num_heads=num_heads,
            expansion=4.0,
            is_causal=False,
            init_type="lecun_normal",
            norm_type="pre",
            norm_eps=1e-5,
            pos_emb_type="none",  # No RoPE — graph encoder handles locality
            forward_dtype="float32",
            H_cycles=h_cycles,
            L_cycles=l_cycles,
        )
        self.backbone = HierarchicalReasoningModel(cfg)

        # Output heads
        self.head_norm = nn.LayerNorm(hidden)
        self.policy_head = nn.Linear(hidden, 1, bias=False)  # per-point logit
        self.pass_head = nn.Linear(hidden, 1)  # pass-move logit
        self.value_head = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Linear(hidden, 1),
        )

    def _embed(
        self,
        stones: torch.Tensor,
        node_type: torch.Tensor,
        coords: torch.Tensor,
    ) -> torch.Tensor:
        """Embed board into node features (B, 302, D)."""
        ids = stones.to(torch.long).clamp(-1, 1) + 1  # -> {0, 1, 2}
        x = self.stone_emb(ids)  # (B, 302, D)
        x = x + self.type_emb(node_type)  # broadcast (302, D)
        x = x + self.coord_proj(coords)  # broadcast (302, D)
        return x

    def _init_carry(self, x: torch.Tensor) -> HierarchicalReasoningModelCarry:
        return HierarchicalReasoningModelCarry(
            z_H=torch.zeros_like(x),
            z_L=torch.zeros_like(x),
        )

    def forward(
        self,
        stones: torch.Tensor,
        edge_index: torch.Tensor,
        node_type: torch.Tensor,
        coords: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            stones: (B, 302) int values in {-1, 0, 1}
            edge_index: (2, E) int64 graph edges
            node_type: (302,) int64 node types
            coords: (302, 3) float32 3D coordinates
        Returns:
            logits: (B, 303) policy logits
            v:      (B, 1)   value in [-1, 1]
        """
        # Embed
        x = self._embed(stones, node_type, coords)  # (B, 302, D)

        # Graph encoding (local structure)
        x = self.graph_encoder(x, edge_index, self.num_points)  # (B, 302, D)

        # Prepend CLS
        B = x.size(0)
        cls = self.cls_token.expand(B, -1, -1)  # (B, 1, D)
        x = torch.cat([cls, x], dim=1)  # (B, 303, D)

        # HRM backbone
        carry = self._init_carry(x)
        _, z = self.backbone(x, carry, cache=None)  # z: (B, 303, D)
        z = self.head_norm(z)

        cls_tok = z[:, 0]  # (B, D)
        board_tok = z[:, 1:]  # (B, 302, D)

        board_logits = self.policy_head(board_tok).squeeze(-1)  # (B, 302)
        pass_logit = self.pass_head(cls_tok)  # (B, 1)
        logits = torch.cat([board_logits, pass_logit], dim=1)  # (B, 303)

        v = torch.tanh(self.value_head(cls_tok))  # (B, 1)
        return logits, v
