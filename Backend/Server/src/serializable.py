from pydantic import BaseModel, UUID4
from typing import Optional

class ImageGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None

class MeshGenerationRequest(BaseModel):
    project_id: UUID4
    perspective: bool   # perspective or object
    textured: bool      # textured or non-textured
    #meshing: bool      # pc or mesh