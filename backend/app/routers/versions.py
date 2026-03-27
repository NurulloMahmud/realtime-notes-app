import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.schemas.version import VersionResponse
from app.services.versions import get_versions, get_version_by_id
from app.services.notes import get_note_by_id, user_can_access, update_note
from app.dependencies import get_current_user

router = APIRouter(prefix="/notes", tags=["versions"])


@router.get("/{note_id}/versions", response_model=list[VersionResponse])
async def list_versions(
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

    versions = await get_versions(db, note_id)
    return [
        VersionResponse(
            id=v.id,
            note_id=v.note_id,
            edited_by=v.edited_by,
            content=v.content,
            created_at=v.created_at,
            editor_username=v.editor.username if v.editor else None,
        )
        for v in versions
    ]


@router.post("/{note_id}/versions/{version_id}/restore", response_model=VersionResponse)
async def restore_version(
    note_id: uuid.UUID,
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    can_access = await user_can_access(db, note, current_user.id)
    if not can_access:
        raise HTTPException(status_code=403, detail="Access denied")

    version = await get_version_by_id(db, version_id)
    if not version or version.note_id != note_id:
        raise HTTPException(status_code=404, detail="Version not found")

    await update_note(db, note, current_user.id, title=None, content=version.content)
    return VersionResponse(
        id=version.id,
        note_id=version.note_id,
        edited_by=current_user.id,
        content=version.content,
        created_at=datetime.utcnow(),
        editor_username=current_user.username,
    )
