from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import torch
from torch import nn

from .transformer import Cache, Transformer, TransformerConfig

HierarchicalReasoningModelCarry = dict[str, torch.Tensor]


@dataclass
class HierarchicalReasoningModelCache:
    H: List[List[Cache]]
    L: List[List[Cache]]


class HierarchicalReasoningModelConfig(TransformerConfig):
    H_cycles: int
    L_cycles: int

    # Change some Transformer config of H-level
    # TODO: Try asymmetric H and L module, such as different size, hidden dims, architecture, attention type, etc.
    H_override: Dict[str, Any] = {}


class HierarchicalReasoningModelRecurrentBlock(nn.Module):
    def __init__(self, config: HierarchicalReasoningModelConfig) -> None:
        super().__init__()
        self.core = Transformer(config)

        # Create cache function
        self.create_cache = self.core.create_cache

    def forward(
        self, hidden_states: torch.Tensor, input_injection: torch.Tensor, **kwargs
    ) -> torch.Tensor:
        # Input injection (add)
        # TODO: Try better alternatives, such as GRU / gating in the following papers
        # Alternatively, "fixed" gating that does not depend on hidden state is also worth trying
        # E.g. only depends on position and index of hidden_states dimension
        # https://arxiv.org/pdf/1910.06764
        # https://arxiv.org/pdf/2202.10447

        # TODO: Asymmetric fusion is also worth trying. assign different number of tokens to H and L.
        return self.core(hidden_states + input_injection, **kwargs)


class HierarchicalReasoningModel(nn.Module):
    def __init__(self, config: HierarchicalReasoningModelConfig) -> None:
        super().__init__()
        self.H_cycles = config.H_cycles
        self.L_cycles = config.L_cycles

        # Reasoning Layers
        self.H_level = HierarchicalReasoningModelRecurrentBlock(
            HierarchicalReasoningModelConfig(
                **(config.model_dump() | config.H_override)
            )
        )
        self.L_level = HierarchicalReasoningModelRecurrentBlock(config)

        # Create cache function
        self.create_cache = lambda **kwargs: HierarchicalReasoningModelCache(
            H=[self.H_level.create_cache(**kwargs) for _i in range(self.H_cycles)],
            L=[
                self.L_level.create_cache(**kwargs)
                for _i in range(self.H_cycles * self.L_cycles)
            ],
        )

    def forward(
        self,
        x: torch.Tensor,
        carry: HierarchicalReasoningModelCarry,
        cache: Optional[HierarchicalReasoningModelCache] = None,
    ) -> Tuple[HierarchicalReasoningModelCarry, torch.Tensor]:
        # Forward iterations
        with torch.no_grad():
            z_H, z_L = carry["z_H"], carry["z_L"]

            for _i in range(self.H_cycles * self.L_cycles - 1):
                z_L = self.L_level(
                    z_L, z_H + x, cache=cache.L[_i] if cache is not None else None
                )
                if (_i + 1) % self.L_cycles == 0:
                    z_H = self.H_level(
                        z_H,
                        z_L,
                        cache=(
                            cache.H[_i // self.L_cycles] if cache is not None else None
                        ),
                    )

        assert not z_H.requires_grad and not z_L.requires_grad

        # 1-step grad
        z_L = self.L_level(
            z_L, z_H + x, cache=cache.L[-1] if cache is not None else None
        )
        z_H = self.H_level(z_H, z_L, cache=cache.H[-1] if cache is not None else None)

        return (
            HierarchicalReasoningModelCarry(z_H=z_H.detach(), z_L=z_L.detach()),
            z_H,
        )  # Ensure no gradient moves across carry
