import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.models.version import NoteVersion
from app.config import settings


async def save_version(db: AsyncSession, note_id: uuid.UUID, user_id: uuid.UUID, content: str):
    version = NoteVersion(note_id=note_id, edited_by=user_id, content=content)
    db.add(version)
    await db.flush()
    await prune_versions(db, note_id)


async def prune_versions(db: AsyncSession, note_id: uuid.UUID):
    result = await db.execute(
        select(NoteVersion.id)
        .where(NoteVersion.note_id == note_id)
        .order_by(NoteVersion.created_at.desc())
        .offset(settings.VERSION_HISTORY_LIMIT)
    )
    old_ids = result.scalars().all()
    if old_ids:
        await db.execute(delete(NoteVersion).where(NoteVersion.id.in_(old_ids)))


async def get_versions(db: AsyncSession, note_id: uuid.UUID) -> list[NoteVersion]:
    result = await db.execute(
        select(NoteVersion)
        .options(selectinload(NoteVersion.editor))
        .where(NoteVersion.note_id == note_id)
        .order_by(NoteVersion.created_at.desc())
        .limit(settings.VERSION_HISTORY_LIMIT)
    )
    return result.scalars().all()


async def get_version_by_id(db: AsyncSession, version_id: uuid.UUID) -> Optional[NoteVersion]:
    result = await db.execute(select(NoteVersion).where(NoteVersion.id == version_id))
    return result.scalar_one_or_none()
