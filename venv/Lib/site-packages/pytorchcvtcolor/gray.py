import torch
import torch.nn as nn

from .rgb import bgr_to_rgb

def gray_to_rgb(image: torch.Tensor) -> torch.Tensor:
    if image.dim() < 3 or image.size(-3) != 1:
        raise ValueError(f"Input size must have a shape of (*, 1, H, W). " f"Got {image.shape}.")
    rgb: torch.Tensor = torch.cat([image, image, image], dim=-3)
    return rgb


def rgb_to_gray(
    image: torch.Tensor, rgb_weights: torch.Tensor = torch.tensor([0.299, 0.587, 0.114])
) -> torch.Tensor:
    if len(image.shape) < 3 or image.shape[-3] != 3:
        raise ValueError(f"Input size must have a shape of (*, 3, H, W). Got {image.shape}")
    r: torch.Tensor = image[..., 0:1, :, :]
    g: torch.Tensor = image[..., 1:2, :, :]
    b: torch.Tensor = image[..., 2:3, :, :]
    w_r, w_g, w_b = rgb_weights.to(image).unbind()
    return w_r * r + w_g * g + w_b * b


def bgr_to_gray(image: torch.Tensor) -> torch.Tensor:
    if len(image.shape) < 3 or image.shape[-3] != 3:
        raise ValueError(f"Input size must have a shape of (*, 3, H, W). Got {image.shape}")

    image_rgb = bgr_to_rgb(image)
    return rgb_to_gray(image_rgb)
