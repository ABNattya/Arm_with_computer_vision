
import torch
import torch.nn as nn
import numpy as np
from .rgb import bgr_to_rgb,rgb_to_bgr
from .gray import gray_to_rgb,rgb_to_gray,bgr_to_gray
from .hsv import rgb_to_hsv,hsv_to_rgb
from .ycbcr import rgb_to_ycbcr, ycbcr_to_rgb


def cvt_color(image: torch.Tensor,code:str)-> torch.Tensor:
    """ main function for color convertor """
    if not isinstance(image,torch.Tensor):
        raise TypeError(f"Input type is not a torch.Tensor. Got {type(image)}")
    if code == 'COLOR_RGB2GRAY':
        return rgb_to_gray(image)
    elif code == 'COLOR_GRAY2RGB':
        return gray_to_rgb(image)
    elif code == 'COLOR_RGB2BGR':
        return rgb_to_bgr(image)   
    elif code == 'COLOR_BGR2RGB':
        return bgr_to_rgb(image)  
    elif code == 'COLOR_BGR2GAY':
        return bgr_to_gray(image)          
    elif code == 'COLOR_RGB2HSV':
        return rgb_to_hsv(image)     
    elif code == 'COLOR_HSV2RGB':
        return hsv_to_rgb(image)     
    elif code == 'COLOR_RGB2YCBCR':
        return rgb_to_ycbcr(image)    
    elif code == 'COLOR_YCBCR2RGB':
        return ycbcr_to_rgb(image) 
    else:
        raise ValueError("Inavlid color convert code")



class CvtColor(nn.Module):
    def forward(self,image:torch.Tensor,code:str):
        return cvt_color(image,code)