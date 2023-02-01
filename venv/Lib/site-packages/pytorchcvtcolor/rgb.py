from typing import cast, Union

import torch
import torch.nn as nn


def rgb_to_bgr(image: torch.Tensor) -> torch.Tensor:
    if len(image.shape) < 3 or image.shape[-3] != 3:
        raise ValueError(f"Input size must have a shape of (*, 3, H, W).Got {image.shape}")

    return bgr_to_rgb(image)


def bgr_to_rgb(image: torch.Tensor) -> torch.Tensor:

    if len(image.shape) < 3 or image.shape[-3] != 3:
        raise ValueError(f"Input size must have a shape of (*, 3, H, W).Got {image.shape}")
    out: torch.Tensor = image.flip(-3)
    return out


def rgb_to_rgba(image: torch.Tensor, alpha_val: Union[float, torch.Tensor]) -> torch.Tensor:
    if len(image.shape) < 3 or image.shape[-3] != 3:
        raise ValueError(f"Input size must have a shape of (*, 3, H, W).Got {image.shape}")

    if not isinstance(alpha_val, (float, torch.Tensor)):
        raise TypeError(f"alpha_val type is not a float or torch.Tensor. Got {type(alpha_val)}")

    r, g, b = torch.chunk(image, image.shape[-3], dim=-3)

    a: torch.Tensor = cast(torch.Tensor, alpha_val)

    if isinstance(alpha_val, float):
        a = torch.full_like(r, fill_value=float(alpha_val))

    return torch.cat([r, g, b, a], dim=-3)


def bgr_to_rgba(image: torch.Tensor, alpha_val: Union[float, torch.Tensor]) -> torch.Tensor:
    if len(image.shape) < 3 or image.shape[-3] != 3:
        raise ValueError(f"Input size must have a shape of (*, 3, H, W).Got {image.shape}")

    if not isinstance(alpha_val, (float, torch.Tensor)):
        raise TypeError(f"alpha_val type is not a float or torch.Tensor. Got {type(alpha_val)}")

    # convert first to RGB, then add alpha channel
    x_rgb: torch.Tensor = bgr_to_rgb(image)
    return rgb_to_rgba(x_rgb, alpha_val)


def rgba_to_rgb(image: torch.Tensor) -> torch.Tensor:
    if len(image.shape) < 3 or image.shape[-3] != 4:
        raise ValueError(f"Input size must have a shape of (*, 4, H, W).Got {image.shape}")

    # unpack channels
    r, g, b, a = torch.chunk(image, image.shape[-3], dim=-3)

    # compute new channels
    a_one = torch.tensor(1.0) - a
    r_new: torch.Tensor = a_one * r + a * r
    g_new: torch.Tensor = a_one * g + a * g
    b_new: torch.Tensor = a_one * b + a * b

    return torch.cat([r_new, g_new, b_new], dim=-3)


def rgba_to_bgr(image: torch.Tensor) -> torch.Tensor:
    if len(image.shape) < 3 or image.shape[-3] != 4:
        raise ValueError(f"Input size must have a shape of (*, 4, H, W).Got {image.shape}")

    # convert to RGB first, then to BGR
    x_rgb: torch.Tensor = rgba_to_rgb(image)
    return rgb_to_bgr(x_rgb)