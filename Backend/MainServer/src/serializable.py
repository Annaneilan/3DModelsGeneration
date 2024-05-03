from pydantic import BaseModel, UUID4
from typing import Optional

class ImageGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None

class MeshGenerationRequest(BaseModel):
    image_uuid: UUID4