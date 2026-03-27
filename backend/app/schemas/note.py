import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class NoteCreate(BaseModel):
    title: str
    content: str = ""

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if not 1 <= len(v) <= 255:
            raise ValueError("title must be 1-255 characters")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if len(v) > 50000:
            raise ValueError("content must not exceed 50000 characters")
        return v


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if v is not None and not 1 <= len(v) <= 255:
            raise ValueError("title must be 1-255 characters")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if v is not None and len(v) > 50000:
            raise ValueError("content must not exceed 50000 characters")
        return v


class CollaboratorInNote(BaseModel):
    id: uuid.UUID
    username: str
    email: str

    model_config = {"from_attributes": True}


class NoteResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteDetailResponse(NoteResponse):
    owner_username: str = ""
    collaborators: list[CollaboratorInNote] = []
