"""Lightweight graph message-passing layers for spherical Go.

Uses precomputed edge_index in COO format. No external GNN library needed.
The graph is small (302 nodes, ~1200 edges) so scatter-based ops are fine.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn


class GraphConvBlock(nn.Module):
    """Simple message-passing block with residual connection.

    For each node i:
        h_i' = h_i + MLP(Aggregate({h_j : j in N(i)}) + h_i)

    Aggregation is mean-pooling over neighbors.
    """

    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        self.linear_msg = nn.Linear(hidden_size, hidden_size)
        self.linear_upd = nn.Linear(hidden_size * 2, hidden_size)
        self.norm = nn.LayerNorm(hidden_size)

    def forward(
        self, x: torch.Tensor, edge_index: torch.Tensor, num_nodes: int
    ) -> torch.Tensor:
        """
        Args:
            x: (B, N, D) node features
            edge_index: (2, E) int64 COO edge list (same for all items in batch)
            num_nodes: N
        Returns:
            (B, N, D) updated node features
        """
        src, dst = edge_index  # (E,), (E,)
        B, N, D = x.shape

        # Gather source node features: (B, E, D)
        x_src = x[:, src]

        # Transform messages
        msgs = self.linear_msg(x_src)  # (B, E, D)

        # Aggregate by destination (mean pooling)
        # Use scatter_add then divide by degree
        agg = torch.zeros(B, N, D, device=x.device, dtype=x.dtype)
        dst_expanded = dst.unsqueeze(0).unsqueeze(-1).expand(B, -1, D)
        agg.scatter_add_(1, dst_expanded, msgs)

        # Degree normalization
        deg = torch.zeros(N, device=x.device, dtype=x.dtype)
        deg.scatter_add_(
            0, dst, torch.ones(dst.shape[0], device=x.device, dtype=x.dtype)
        )
        deg = deg.clamp(min=1.0)
        agg = agg / deg.unsqueeze(0).unsqueeze(-1)

        # Update: concat aggregated + self, project, residual
        combined = torch.cat([agg, x], dim=-1)  # (B, N, 2D)
        out = self.linear_upd(combined)  # (B, N, D)
        out = F.gelu(out)

        return self.norm(x + out)


class GraphEncoder(nn.Module):
    """Stack of GraphConvBlocks for encoding the spherical board."""

    def __init__(self, hidden_size: int, num_layers: int = 2) -> None:
        super().__init__()
        self.layers = nn.ModuleList(
            [GraphConvBlock(hidden_size) for _ in range(num_layers)]
        )

    def forward(
        self, x: torch.Tensor, edge_index: torch.Tensor, num_nodes: int
    ) -> torch.Tensor:
        for layer in self.layers:
            x = layer(x, edge_index, num_nodes)
        return x
