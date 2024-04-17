import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler, DiffusionPipeline

def load_2_1():
    model_id = "stabilityai/stable-diffusion-2-1"

    # Use the DPMSolverMultistepScheduler (DPM-Solver++) scheduler here instead
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to("cuda")
    
    return pipe