import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class CollaboratorAdd(BaseModel):
    user_id: Optional[uuid.UUID] = None
    email: Optional[EmailStr] = None


class CollaboratorResponse(BaseModel):
    id: uuid.UUID
    note_id: uuid.UUID
    user_id: uuid.UUID
    added_at: datetime
    username: str
    email: str

    model_config = {"from_attributes": True}
