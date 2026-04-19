"""Quiz model — stores individual quiz items tied to generated content."""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4

from app.core.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    generated_content_id: Mapped[str] = mapped_column(
        String, ForeignKey("generated_content.id", ondelete="CASCADE")
    )

    question: Mapped[str] = mapped_column(String(2000))
    options: Mapped[list] = mapped_column(JSON)       # ["a","b","c","d"]
    correct_index: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(String(2000), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    generated_content = relationship("GeneratedContent", back_populates="quizzes")