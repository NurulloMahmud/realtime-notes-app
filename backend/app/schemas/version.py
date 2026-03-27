import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class VersionResponse(BaseModel):
    id: uuid.UUID
    note_id: uuid.UUID
    edited_by: uuid.UUID
    content: str
    created_at: datetime
    editor_username: Optional[str] = None

    model_config = {"from_attributes": True}
