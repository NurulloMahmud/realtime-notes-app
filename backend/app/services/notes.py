import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.models.note import Note
from app.models.collaborator import NoteCollaborator
from app.models.user import User
from app.services.versions import save_version


async def create_note(db: AsyncSession, owner_id: uuid.UUID, title: str, content: str) -> Note:
    note = Note(owner_id=owner_id, title=title, content=content)
    db.add(note)
    await db.flush()
    await save_version(db, note.id, owner_id, content)
    await db.commit()
    await db.refresh(note)
    return note


async def get_user_notes(db: AsyncSession, user_id: uuid.UUID) -> list[Note]:
    collab_subquery = select(NoteCollaborator.note_id).where(NoteCollaborator.user_id == user_id)
    result = await db.execute(
        select(Note).where(or_(Note.owner_id == user_id, Note.id.in_(collab_subquery)))
    )
    return result.scalars().all()


async def get_note_with_collaborators(db: AsyncSession, note_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Note]:
    result = await db.execute(
        select(Note)
        .options(
            selectinload(Note.collaborators).selectinload(NoteCollaborator.user),
            selectinload(Note.owner),
        )
        .where(Note.id == note_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        return None
    if note.owner_id != user_id and not any(c.user_id == user_id for c in note.collaborators):
        return None
    return note


async def update_note(db: AsyncSession, note: Note, user_id: uuid.UUID, title: Optional[str], content: Optional[str]) -> Note:
    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
        await save_version(db, note.id, user_id, content)
    note.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(note)
    return note


async def delete_note(db: AsyncSession, note: Note):
    await db.delete(note)
    await db.commit()


async def get_note_by_id(db: AsyncSession, note_id: uuid.UUID) -> Optional[Note]:
    result = await db.execute(select(Note).where(Note.id == note_id))
    return result.scalar_one_or_none()


async def user_can_access(db: AsyncSession, note: Note, user_id: uuid.UUID) -> bool:
    if note.owner_id == user_id:
        return True
    result = await db.execute(
        select(NoteCollaborator).where(
            NoteCollaborator.note_id == note.id,
            NoteCollaborator.user_id == user_id,
        )
    )
    return result.scalar_one_or_none() is not None
