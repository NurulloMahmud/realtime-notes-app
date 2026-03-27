import uuid
from datetime import datetime
from sqlalchemy import Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class NoteVersion(Base):
    __tablename__ = "note_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    note_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("notes.id"), nullable=False)
    edited_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    note: Mapped["Note"] = relationship("Note", back_populates="versions")
    editor: Mapped["User"] = relationship("User", back_populates="versions")
