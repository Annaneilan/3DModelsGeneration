import io
import uuid
from typing import Union, Any
from enum import IntEnum

class ResourceStatus(IntEnum):
    PENDING = 0
    AVAILABLE = 1
    NOT_AVAILABLE = 2

class RequestedResource:
    def __init__(
        self,
        project_id: uuid.UUID,
        status: ResourceStatus = ResourceStatus.PENDING,
        data: io.BytesIO = None
    ) -> None:
        self.id = project_id
        self.status = status
        self.data = data