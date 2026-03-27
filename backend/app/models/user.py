import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    notes: Mapped[list["Note"]] = relationship("Note", back_populates="owner", cascade="all, delete-orphan")
    collaborations: Mapped[list["NoteCollaborator"]] = relationship("NoteCollaborator", back_populates="user", cascade="all, delete-orphan")
    versions: Mapped[list["NoteVersion"]] = relationship("NoteVersion", back_populates="editor")
