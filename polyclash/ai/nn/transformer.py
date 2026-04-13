import math
from typing import List, Literal, Optional

import torch
import torch.nn.functional as F
from pydantic import BaseModel
from torch import nn

from .layers import Attention, Cache, RotaryEmbedding2D, SwiGLU, find_multiple


class InitConfig(BaseModel):
    in_std: float

    attn_out_std: float
    ff_out_std: float


class TransformerConfig(BaseModel):
    # Input config
    beginning_tokens: int
    height: int
    width: int

    # Transformer config
    n_layers: int

    hidden_size: int
    num_heads: int
    expansion: float
    is_causal: bool

    init_type: Literal["fixed_normal", "lecun_normal", "megatron"]
    init_std: Optional[float] = None

    norm_type: Literal["pre", "post", "hybrid"]
    norm_eps: float

    pos_emb_type: Literal["rope", "none"]
    rope_theta: Optional[float] = None

    forward_dtype: str = "bfloat16"

    # [Computed properties]
    @property
    def dtype(self):
        return getattr(torch, self.forward_dtype)

    @property
    def intermediate_size(self):
        # Automatic compute "intermediate_size" from "expansion"
        # NOTE: The formula is to match the number of GLU parameters to a vanilla Transformer with same expansion
        return find_multiple(round(self.expansion * self.hidden_size * 2 / 3), 256)

    @property
    def init_config(self):
        match self.init_type:
            case "fixed_normal":
                in_std = attn_out_std = ff_out_std = (
                    self.init_std if self.init_std is not None else 0.02
                )  # defaults to 0.02, as in OLMo 2
            case "lecun_normal":
                in_std = attn_out_std = 1.0 / math.sqrt(self.hidden_size)
                ff_out_std = 1.0 / math.sqrt(self.intermediate_size)
            case "megatron":
                in_std = (
                    self.init_std
                    if self.init_std is not None
                    else 1.0 / math.sqrt(self.hidden_size)
                )
                attn_out_std = ff_out_std = in_std / math.sqrt(2.0 * self.n_layers)
            case _:
                raise NotImplementedError()

        return InitConfig(
            in_std=in_std, attn_out_std=attn_out_std, ff_out_std=ff_out_std
        )


class TransformerBlock(nn.Module):
    def __init__(self, config: TransformerConfig) -> None:
        super().__init__()
        self.attn = Attention(
            hidden_size=config.hidden_size,
            head_dim=config.hidden_size // config.num_heads,
            num_heads=config.num_heads,
            num_key_value_heads=config.num_heads,
            is_causal=config.is_causal,
            qkv_norm=config.norm_type == "hybrid",
            qkv_norm_eps=config.norm_eps,
            init_std_in=config.init_config.in_std,
            init_std_out=config.init_config.attn_out_std,
            dtype=config.dtype,
        )
        self.mlp = SwiGLU(
            hidden_size=config.hidden_size,
            intermediate_size=config.intermediate_size,
            init_std_in=config.init_config.in_std,
            init_std_out=config.init_config.ff_out_std,
            dtype=config.dtype,
        )

        self.forward = getattr(
            self, f"_forward_{config.norm_type}"
        )  # Avoid branching logic in "forward" for torch.compile compatibility
        self.norm = lambda x: F.rms_norm(x, (x.shape[-1],), eps=config.norm_eps)

    # [Forward logic]
    def _forward_pre(self, x: torch.Tensor, **seq_info) -> torch.Tensor:  # Pre Norm
        x = x + self.attn(self.norm(x), **seq_info)
        return x + self.mlp(self.norm(x))

    def _forward_post(self, x: torch.Tensor, **seq_info) -> torch.Tensor:  # Post Norm
        x = self.norm(x + self.attn(x, **seq_info))
        return self.norm(x + self.mlp(x))

    def _forward_hybrid(
        self, x: torch.Tensor, **seq_info
    ) -> torch.Tensor:  # Hybrid Norm
        # QKVNorm is already added on Attention module creation
        x = self.norm(x + self.attn(x, **seq_info))
        return x + self.mlp(x)


class Transformer(nn.Module):
    def __init__(self, config: TransformerConfig) -> None:
        super().__init__()
        # Position embeddings
        if config.pos_emb_type == "rope":
            assert config.rope_theta is not None
            self.rotary_emb = RotaryEmbedding2D(
                config.hidden_size // config.num_heads,
                config.beginning_tokens,
                config.height,
                config.width,
                base=config.rope_theta,
            )

        # Layers
        self.layers = nn.ModuleList(
            [TransformerBlock(config) for _layer_idx in range(config.n_layers)]
        )

        # Use final norm only for prenorm
        self.norm_f = lambda x: x
        if config.norm_type == "pre":
            self.norm_f = lambda x: F.rms_norm(x, (x.shape[-1],), eps=config.norm_eps)

        # Create cache function
        self.create_cache = lambda **kwargs: [
            Cache(
                **kwargs,
                num_heads=config.num_heads,
                head_dim=config.hidden_size // config.num_heads,
            )
            for _i in range(config.n_layers)
        ]

    def forward(
        self, x: torch.Tensor, cache: Optional[List[Cache]] = None
    ) -> torch.Tensor:
        # position ids
        # NOTE: if there are previous tokens in cache, current position ids should be offseted by number of previous tokens, otherwise start from 0
        position_ids = None
        if cache is not None:
            offset = cache[0].lengths
            position_ids = offset.unsqueeze(-1) + torch.arange(
                0, x.shape[-2], dtype=offset.dtype, device=offset.device
            )
        # get RoPE cos and sin at position_ids
        cos_sin = None
        if hasattr(self, "rotary_emb"):
            cos_sin = self.rotary_emb(position_ids)
        # Forward layers
        for layer_id, layer in enumerate(self.layers):
            x = layer(
                x, cos_sin=cos_sin, cache=cache[layer_id] if cache is not None else None
            )

        return self.norm_f(x)
