import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.schemas.collaborator import CollaboratorAdd, CollaboratorResponse
from app.services import collaborators as collab_service
from app.services.notes import get_note_by_id, user_can_access
from app.dependencies import get_current_user

router = APIRouter(prefix="/notes", tags=["collaborators"])


@router.post("/{note_id}/collaborators", response_model=CollaboratorResponse, status_code=status.HTTP_201_CREATED)
async def add_collaborator(
    note_id: uuid.UUID,
    data: CollaboratorAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can add collaborators")

    target_user = await collab_service.find_user_by_email_or_id(db, data.user_id, data.email)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Owner cannot be added as a collaborator")

    existing = await collab_service.get_collaborator(db, note_id, target_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="User is already a collaborator")

    collab = await collab_service.add_collaborator(db, note_id, target_user.id)
    return CollaboratorResponse(
        id=collab.id,
        note_id=collab.note_id,
        user_id=collab.user_id,
        added_at=collab.added_at,
        username=target_user.username,
        email=target_user.email,
    )


@router.get("/{note_id}/collaborators", response_model=list[CollaboratorResponse])
async def list_collaborators(
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    can_access = await user_can_access(db, note, current_user.id)
    if not can_access:
        raise HTTPException(status_code=403, detail="Access denied")

    collabs = await collab_service.get_collaborators(db, note_id)
    return [
        CollaboratorResponse(
            id=c.id,
            note_id=c.note_id,
            user_id=c.user_id,
            added_at=c.added_at,
            username=c.user.username,
            email=c.user.email,
        )
        for c in collabs
    ]


@router.delete("/{note_id}/collaborators/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_collaborator(
    note_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can remove collaborators")

    collab = await collab_service.get_collaborator(db, note_id, user_id)
    if not collab:
        raise HTTPException(status_code=404, detail="Collaborator not found")
    await collab_service.remove_collaborator(db, collab)
