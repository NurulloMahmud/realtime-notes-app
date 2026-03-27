import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    owner: Mapped["User"] = relationship("User", back_populates="notes")
    collaborators: Mapped[list["NoteCollaborator"]] = relationship("NoteCollaborator", back_populates="note", cascade="all, delete-orphan")
    versions: Mapped[list["NoteVersion"]] = relationship("NoteVersion", back_populates="note", cascade="all, delete-orphan", order_by="NoteVersion.created_at.desc()")
