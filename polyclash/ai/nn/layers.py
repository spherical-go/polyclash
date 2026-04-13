import math
import warnings
from typing import Any, Dict, Optional, Sequence, Tuple

import torch
import torch.nn.functional as F
from einops import rearrange
from torch import nn

from .common import trunc_normal_init_

_FLASH_OK = False
flash_attn_func = None
flash_attn_with_kvcache = None
try:
    from flash_attn_interface import (  # type: ignore[import]
        flash_attn_func,
        flash_attn_with_kvcache,
    )

    _FLASH_OK = True
except ImportError:
    try:
        from flash_attn import (  # type: ignore[import]
            flash_attn_func,
            flash_attn_with_kvcache,
        )

        _FLASH_OK = True
        warnings.warn("FlashAttention 3 not found. Fallback to FlashAttention 2.")
    except ImportError:
        warnings.warn("FlashAttention not available. Using PyTorch SDPA fallback.")


Carry = Dict[str, Any]
CosSin = Tuple[torch.Tensor, torch.Tensor]


def find_multiple(a, b):
    return (-(a // -b)) * b


def rotate_half(x: torch.Tensor):
    """Rotates half the hidden dims of the input."""
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(x: torch.Tensor, cos_sin: CosSin):
    # x:   [..., seq_len, num_heads, head_dim]
    # cos, sin: [seq_len, head_dim] OR [..., seq_len, head_dim]
    # Use FP32 RoPE, as in Transformers OLMo and FlashAttention
    #
    # https://github.com/huggingface/transformers/blob/v4.55.4/src/transformers/models/olmo/modular_olmo.py#L139-L152
    # https://github.com/Dao-AILab/flash-attention/blob/v2.8.3/csrc/flash_attn/src/rotary.h#L126-L133
    cos, sin = cos_sin
    return ((x * cos.unsqueeze(-2)) + (rotate_half(x) * sin.unsqueeze(-2))).to(x.dtype)


class RotaryEmbedding2D(torch.nn.Module):
    def __init__(self, head_dim, beginning_tokens, height, width, base, **kwargs):
        super().__init__()
        # RoPE
        assert head_dim % 2 == 0, "dim must be multiples of 2."
        dim = head_dim // 2

        inv_freq = 1.0 / (
            base ** (torch.arange(0, dim, 2, dtype=torch.float32, **kwargs) / dim)
        )
        t = torch.arange(
            beginning_tokens + max(width, height), dtype=torch.float32, **kwargs
        )
        freqs = torch.outer(t, inv_freq)

        # Different from paper, but it uses a different permutation in order to obtain the same calculation
        emb = torch.cat((freqs, freqs), dim=-1)

        # Ids of 2D
        id_begin = torch.arange(beginning_tokens, dtype=torch.long)
        ids = torch.stack(
            (
                torch.cat(
                    (
                        id_begin,
                        beginning_tokens
                        + torch.arange(height * width, dtype=torch.long) // width,
                    )
                ),
                torch.cat(
                    (
                        id_begin,
                        beginning_tokens
                        + torch.arange(height * width, dtype=torch.long) % width,
                    )
                ),
            ),
            dim=-1,
        )

        self.cos_cached = nn.Buffer(
            emb.cos()[ids].view(ids.shape[0], -1), persistent=False
        )
        self.sin_cached = nn.Buffer(
            emb.sin()[ids].view(ids.shape[0], -1), persistent=False
        )
        self.seq_len = beginning_tokens + height * width

    def forward(self, position_ids: torch.Tensor):
        if position_ids is not None:
            return self.cos_cached[position_ids], self.sin_cached[position_ids]

        return self.cos_cached, self.sin_cached


class LinearInit(nn.Module):
    def __init__(
        self,
        in_features: int,
        out_features: int,
        bias: bool,
        batch_out_features: Sequence[int] = (),
        init_std: Optional[float] = None,
        spectral_enable: bool = True,
        **kwargs,
    ):
        super().__init__()
        self.in_features = in_features
        # Truncated LeCun normal init
        if init_std is None:
            init_std = 1.0 / (in_features**0.5)

        # Parameters
        self.weight = nn.Parameter(
            trunc_normal_init_(
                torch.empty(
                    (math.prod(batch_out_features) * out_features, in_features),
                    **kwargs,
                ),
                std=init_std,
            )  # pyright: ignore[reportArgumentType]
        )
        self.bias = None
        if bias:
            # Zero init bias
            self.bias = nn.Parameter(
                torch.zeros((math.prod(batch_out_features) * out_features,), **kwargs)
            )

        # Spectral (save properties into parameter, to hint the Adams optimizer)
        self.weight.optimizer_spectral_enable = (
            spectral_enable  # pyright: ignore[reportAttributeAccessIssue]
        )
        self.weight.optimizer_spectral_shape = (
            *batch_out_features,
            out_features,
            in_features,
        )  # pyright: ignore[reportAttributeAccessIssue]

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return F.linear(input, self.weight, self.bias)


class ScaledEmbeddingInit(nn.Module):
    def __init__(
        self, num_embeddings: int, embedding_dim: int, init_std: float, **kwargs
    ):
        super().__init__()
        self.scale = 1.0 / init_std

        self.embedding_weight = nn.Parameter(
            trunc_normal_init_(
                torch.empty((num_embeddings, embedding_dim), **kwargs), std=init_std
            )  # pyright: ignore[reportArgumentType]
        )

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return self.scale * F.embedding(input, self.embedding_weight)


class Cache:
    """A static cache layer that stores the key and value states as static tensors. Built for `torch.compile` support."""

    def __init__(
        self,
        max_batch_size: int,
        max_seq_len: int,
        num_heads: int,
        head_dim: int,
        **kwargs,
    ):
        super().__init__()

        self.keys = torch.zeros(
            (max_batch_size, max_seq_len, num_heads, head_dim), **kwargs
        )
        self.values = torch.zeros(
            (max_batch_size, max_seq_len, num_heads, head_dim), **kwargs
        )
        self.lengths = torch.zeros(
            (max_batch_size,), **(kwargs | dict(dtype=torch.int32))
        )


class Attention(nn.Module):
    def __init__(
        self,
        hidden_size,
        head_dim,
        num_heads,
        num_key_value_heads,
        is_causal,
        qkv_norm,
        qkv_norm_eps=None,
        init_std_in=None,
        init_std_out=None,
        **kwargs,
    ):
        super().__init__()

        self.head_dim = head_dim
        self.num_heads = num_heads
        self.num_key_value_heads = num_key_value_heads
        self.is_causal = is_causal
        self.qkv_norm = qkv_norm
        self.qkv_norm_eps = qkv_norm_eps

        self.qkv_proj = LinearInit(
            hidden_size,
            self.head_dim,
            batch_out_features=(self.num_heads + 2 * self.num_key_value_heads,),
            bias=False,
            init_std=init_std_in,
            **kwargs,
        )
        self.o_proj = LinearInit(
            head_dim * num_heads,
            hidden_size,
            bias=False,
            init_std=init_std_out,
            **kwargs,
        )

    def forward(
        self,
        hidden_states: torch.Tensor,
        cos_sin: Optional[CosSin],
        cache: Optional[Cache] = None,
    ) -> torch.Tensor:
        # hidden_states, qkv: [..., seq_len, hidden_size]
        qkv = self.qkv_proj(hidden_states)

        # Split head (last dimension of projected qkv)
        qkv = rearrange(
            qkv,
            "... (h hd) -> ... h hd",
            h=self.num_heads + 2 * self.num_key_value_heads,
        )
        if self.qkv_norm:
            # QKVnorm (on head dimension)
            assert self.qkv_norm_eps is not None
            qkv = F.rms_norm(qkv, (qkv.shape[-1],), eps=self.qkv_norm_eps)

        query, key, value = qkv.split(
            (self.num_heads, self.num_key_value_heads, self.num_key_value_heads), dim=-2
        )
        # query, key, value: [..., seq_len, num_heads, head_dim]
        # RoPE
        if cos_sin is not None:
            query = apply_rotary_pos_emb(query, cos_sin)
            key = apply_rotary_pos_emb(key, cos_sin)

        use_flash = (
            _FLASH_OK
            and hidden_states.is_cuda
            and hidden_states.dtype in (torch.float16, torch.bfloat16)
        )

        seqlen_kv = key.shape[-3]
        if cache is not None and use_flash:
            # With KVCache (flash path)
            # Regardless of auto / non-autoregressive, apply attention based on current concatenated with cache.
            attn_output = flash_attn_with_kvcache(
                q=query,
                k=key,
                v=value,
                k_cache=cache.keys,
                v_cache=cache.values,
                cache_seqlens=cache.lengths,
                causal=False,
            )  # causal can always be False. during AR generation seqlen is 1, so causal masking won't matter.
            # increase cache length
            cache.lengths.add_(seqlen_kv)
        elif cache is None and use_flash:
            # No Cache (flash path)
            attn_output = flash_attn_func(
                q=query, k=key, v=value, causal=self.is_causal
            )
        else:
            # SDPA fallback (no flash)
            # query/key/value: [..., seq_len, num_heads, head_dim] -> [..., num_heads, seq_len, head_dim]
            q = query.transpose(-3, -2)
            k = key.transpose(-3, -2)
            v = value.transpose(-3, -2)
            attn_output = F.scaled_dot_product_attention(
                q, k, v, is_causal=self.is_causal
            )
            # [..., num_heads, seq_len, head_dim] -> [..., seq_len, num_heads, head_dim]
            attn_output = attn_output.transpose(-3, -2)
            if cache is not None:
                # Manually update cache for non-flash path
                batch_size = hidden_states.shape[0]
                for b in range(batch_size):
                    start = cache.lengths[b].item()
                    end = start + seqlen_kv
                    cache.keys[b, start:end] = key[b]
                    cache.values[b, start:end] = value[b]
                cache.lengths.add_(seqlen_kv)

        # attn_output: [..., seq_len, num_heads, head_dim]
        attn_output = rearrange(attn_output, "... h hd -> ... (h hd)")  # type: ignore
        return self.o_proj(attn_output)


class SwiGLU(nn.Module):
    def __init__(
        self,
        hidden_size: int,
        intermediate_size: int,
        init_std_in=None,
        init_std_out=None,
        **kwargs,
    ):
        super().__init__()
        self.gate_up_proj = LinearInit(
            hidden_size,
            intermediate_size,
            batch_out_features=(2,),
            bias=False,
            init_std=init_std_in,
            **kwargs,
        )
        self.down_proj = LinearInit(
            intermediate_size, hidden_size, bias=False, init_std=init_std_out, **kwargs
        )

    def forward(self, x):
        gate, up = self.gate_up_proj(x).chunk(2, dim=-1)
        return self.down_proj(F.silu(gate) * up)


class ScaledPatchify(nn.Module):
    """Convert an image into sequence through ViT patch embedding."""

    def __init__(
        self, hidden_size: int, patch_size: int, channels: int, init_std=None, **kwargs
    ):
        super().__init__()
        patch_ndim = channels * (patch_size**2)
        if init_std is None:
            init_std = 1.0 / (hidden_size**0.5)

        self.patch_size = patch_size
        self.scale = 1.0 / (init_std * math.sqrt(channels * (patch_size**2)))

        # Input head
        self.input_head = LinearInit(
            patch_ndim,
            hidden_size,
            init_std=init_std,
            bias=False,
            spectral_enable=False,
            **kwargs,
        )

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return self.scale * self.input_head(
            rearrange(
                image,
                "... (p h) (q w) c -> ... (p q) (h w c)",
                h=self.patch_size,
                w=self.patch_size,
            )
        )


class Unpatchify(nn.Module):
    """Decode a sequence to image using DiT patch decoding."""

    def __init__(
        self,
        hidden_size: int,
        output_shape: Sequence[int],
        patch_size: int,
        init_std=None,
        **kwargs,
    ):
        super().__init__()
        self.height, self.width, self.channels = output_shape  # HWC
        self.patch_size = patch_size

        # Output head
        self.output_head = LinearInit(
            hidden_size,
            self.patch_size * self.patch_size * self.channels,
            init_std=init_std,
            bias=False,
            spectral_enable=False,
            **kwargs,
        )

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        # decode image
        output = self.output_head(hidden_states)
        output = rearrange(
            output,
            "... (h w) (p q c) -> ... (h p) (w q) c",
            h=self.height // self.patch_size,
            w=self.width // self.patch_size,
            p=self.patch_size,
            q=self.patch_size,
            c=self.channels,
        )

        return output
