"""Schemas for note upload."""

from pydantic import BaseModel, Field
from typing import Optional


class NoteUploadRequest(BaseModel):
    user_email: Optional[str] = Field(None, description="Optional user identifier (email).")
    title: Optional[str] = Field(None, max_length=500)
    raw_text: str = Field(..., min_length=10, description="Raw notes text.")
    source: str = Field("text", description="text | upload | url")


class NoteUploadResponse(BaseModel):
    note_id: str
    title: Optional[str]
    char_count: int
    message: str