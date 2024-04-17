from pydantic import BaseModel
from typing import Optional

class ImageRequestBody(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None