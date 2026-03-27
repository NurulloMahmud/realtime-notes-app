import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.collaborator import NoteCollaborator
from app.models.user import User


async def add_collaborator(db: AsyncSession, note_id: uuid.UUID, user_id: uuid.UUID) -> NoteCollaborator:
    collab = NoteCollaborator(note_id=note_id, user_id=user_id)
    db.add(collab)
    await db.commit()
    await db.refresh(collab)
    return collab


async def get_collaborators(db: AsyncSession, note_id: uuid.UUID) -> list[NoteCollaborator]:
    result = await db.execute(
        select(NoteCollaborator)
        .options(selectinload(NoteCollaborator.user))
        .where(NoteCollaborator.note_id == note_id)
    )
    return result.scalars().all()


async def get_collaborator(db: AsyncSession, note_id: uuid.UUID, user_id: uuid.UUID) -> Optional[NoteCollaborator]:
    result = await db.execute(
        select(NoteCollaborator).where(
            NoteCollaborator.note_id == note_id,
            NoteCollaborator.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def remove_collaborator(db: AsyncSession, collab: NoteCollaborator):
    await db.delete(collab)
    await db.commit()


async def find_user_by_email_or_id(db: AsyncSession, user_id: Optional[uuid.UUID], email: Optional[str]) -> Optional[User]:
    if user_id:
        result = await db.execute(select(User).where(User.id == user_id))
    elif email:
        result = await db.execute(select(User).where(User.email == email))
    else:
        return None
    return result.scalar_one_or_none()
