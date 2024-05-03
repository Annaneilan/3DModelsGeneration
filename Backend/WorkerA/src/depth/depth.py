import cv2
import numpy as np

import torch
import torch.nn.functional as F
from torchvision.transforms import Compose

from .depth_anything.dpt import DepthAnything
from .depth_anything.util.transform import Resize, NormalizeImage, PrepareForNet

class DepthAnythingFacade:
    def __init__(
        self,
        encoder: str = "vitl",
        device: str = "cuda",
    ) -> None:
        # Validate
        if encoder not in ["vits", "vitb", "vitl"]:
            raise ValueError(f"Invalid encoder: {encoder}")
        if device not in ["cuda", "cpu"]:
            raise ValueError(f"Invalid device: {device}")

        # Load model        
        self.model = DepthAnything.from_pretrained(f"LiheYoung/depth_anything_{encoder}14")
        self.model = self.model.to(device).eval()
        
        # Load preprocessing
        self.transform = Compose([
            Resize(
                width=518,
                height=518,
                resize_target=False,
                keep_aspect_ratio=True,
                ensure_multiple_of=14,
                resize_method='lower_bound',
                image_interpolation_method=cv2.INTER_CUBIC,
            ),
            NormalizeImage(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            PrepareForNet(),
        ])
        
        # Misc
        self.device = device
    
    def preprocess(
        self,
        image: np.ndarray
    ) -> np.ndarray:
        image_t = image / 255.0
        image_t = self.transform({"image": image_t})["image"]
        image_t = torch.from_numpy(image_t).unsqueeze(0).to(self.device)
        return image_t
    
    @torch.no_grad()
    def __call__(
        self,
        image: np.ndarray
    ) -> np.ndarray:
        """
        Args:
            image: np.ndarray, shape=(H, W, 3), dtype=np.uint8
        """
        
        # Preprocess
        h, w = image.shape[:2]
        image_pt = self.preprocess(image)
        
        # Inference
        depth_pt = self.model(image_pt)
        
        # Postprocess
        depth_pt = F.interpolate(depth_pt[None], (h, w), mode='bilinear', align_corners=False)[0, 0]
        depth_np = depth_pt.cpu().numpy().astype(np.float32)
        
        return depth_np