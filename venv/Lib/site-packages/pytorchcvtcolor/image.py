
import torch
import torch.nn as nn


def image_to_tensor(image: "np.ndarray", keepdim: bool = True) -> torch.Tensor:

    if len(image.shape) > 4 or len(image.shape) < 2:
        raise ValueError("Input size must be a two, three or four dimensional array")

    input_shape = image.shape
    tensor: torch.Tensor = torch.from_numpy(image)

    if len(input_shape) == 2:
        tensor = tensor.unsqueeze(0)
    elif len(input_shape) == 3:
        tensor = tensor.permute(2, 0, 1)
    elif len(input_shape) == 4:
        tensor = tensor.permute(0, 3, 1, 2)
        keepdim = True  # no need to unsqueeze
    else:
        raise ValueError(f"Cannot process image with shape {input_shape}")

    return tensor.unsqueeze(0) if not keepdim else tensor


def tensor_to_image(tensor: torch.Tensor, keepdim: bool = False) -> "np.ndarray":

    if not isinstance(tensor, torch.Tensor):
        raise TypeError(f"Input type is not a torch.Tensor. Got {type(tensor)}")

    if len(tensor.shape) > 4 or len(tensor.shape) < 2:
        raise ValueError("Input size must be a two, three or four dimensional tensor")

    input_shape = tensor.shape
    image: "np.ndarray" = tensor.cpu().detach().numpy()

    if len(input_shape) == 2:
        pass
    elif len(input_shape) == 3:
        if input_shape[0] == 1:
            image = image.squeeze()
        else:
            image = image.transpose(1, 2, 0)
    elif len(input_shape) == 4:
        image = image.transpose(0, 2, 3, 1)
        if input_shape[0] == 1 and not keepdim:
            image = image.squeeze(0)
        if input_shape[1] == 1:
            image = image.squeeze(-1)
    else:
        raise ValueError(f"Cannot process tensor with shape {input_shape}")

    return image