import torch
import torch.nn.functional as F


def trunc_normal_init_(tensor: torch.Tensor, std: float = 1.0):
    """Fast approximate truncated normal initialization. Fairly accurate."""

    return tensor.normal_().fmod_(3.0).mul_(1.014762601732121 * std)


class GradientReversalFunction(torch.autograd.Function):
    """
    Forwards the tensor as-is, but in .backward() flips the sign of the gradient.
    """

    @staticmethod
    def forward(ctx, x):
        return x

    @staticmethod
    def backward(ctx, grad_output):  # type: ignore
        return -grad_output, None


def image_translation(
    image: torch.Tensor, trans_h: torch.Tensor, trans_w: torch.Tensor
) -> torch.Tensor:
    """Image shape NHWC, trans_h/w shape N"""
    N, H, W, C = image.shape

    grid_n, grid_h, grid_w = torch.meshgrid(
        torch.arange(N, device=image.device),
        torch.arange(H, device=image.device),
        torch.arange(W, device=image.device),
        indexing="ij",
    )
    grid_h = (grid_h + (trans_h + 1).view(N, 1, 1)).clamp(0, H + 1)
    grid_w = (grid_w + (trans_w + 1).view(N, 1, 1)).clamp(0, W + 1)

    image_pad = F.pad(image, [0, 0, 1, 1, 1, 1])
    return image_pad[grid_n, grid_h, grid_w]


class RandomTranslationFunction(torch.autograd.Function):
    """Random translation for an image shaped NHWC. Max translation `max_shift` pixels"""

    @staticmethod
    def forward(ctx, image: torch.Tensor, max_shift: int):
        trans_h, trans_w = torch.randint(
            -max_shift, max_shift + 1, size=(2 * image.shape[0],), device=image.device
        ).chunk(2)
        ctx.save_for_backward(trans_h, trans_w)

        return image_translation(image, trans_h, trans_w)

    @staticmethod
    def backward(ctx, grad_output):  # type: ignore
        trans_h, trans_w = ctx.saved_tensors

        return image_translation(grad_output, -trans_h, -trans_w), None
