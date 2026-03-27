import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.collaborator import NoteCollaborator
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteDetailResponse, CollaboratorInNote
from app.services import notes as note_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(data: NoteCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await note_service.create_note(db, current_user.id, data.title, data.content)


@router.get("", response_model=list[NoteResponse])
async def list_notes(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await note_service.get_user_notes(db, current_user.id)


@router.get("/{note_id}", response_model=NoteDetailResponse)
async def get_note(note_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    note = await note_service.get_note_with_collaborators(db, note_id, current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found or access denied")
    collaborators = [
        CollaboratorInNote(id=c.user.id, username=c.user.username, email=c.user.email)
        for c in note.collaborators
    ]
    return NoteDetailResponse(
        id=note.id,
        owner_id=note.owner_id,
        owner_username=note.owner.username if note.owner else "",
        title=note.title,
        content=note.content,
        created_at=note.created_at,
        updated_at=note.updated_at,
        collaborators=collaborators,
    )


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: uuid.UUID, data: NoteUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    note = await note_service.get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    can_access = await note_service.user_can_access(db, note, current_user.id)
    if not can_access:
        raise HTTPException(status_code=403, detail="Access denied")
    return await note_service.update_note(db, note, current_user.id, data.title, data.content)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    note = await note_service.get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can delete this note")
    await note_service.delete_note(db, note)
