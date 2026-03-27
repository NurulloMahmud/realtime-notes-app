import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class NoteCollaborator(Base):
    __tablename__ = "note_collaborators"
    __table_args__ = (UniqueConstraint("note_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    note_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("notes.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    note: Mapped["Note"] = relationship("Note", back_populates="collaborators")
    user: Mapped["User"] = relationship("User", back_populates="collaborations")
