"""
GeneratedContent model — holds full pipeline output:
concepts, scene plan, translations, status, errors.
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4

from app.core.database import Base


class GeneratedContent(Base):
    __tablename__ = "generated_content"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    note_id: Mapped[str] = mapped_column(String, ForeignKey("notes.id", ondelete="CASCADE"))

    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending | processing | completed | failed
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    concepts: Mapped[dict] = mapped_column(JSON, nullable=True)
    scene_plan: Mapped[dict] = mapped_column(JSON, nullable=True)
    translations: Mapped[dict] = mapped_column(JSON, nullable=True)
    validation_report: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    note = relationship("Note", back_populates="generated_contents")
    quizzes = relationship("Quiz", back_populates="generated_content", cascade="all, delete-orphan")