"""
POST /upload-notes  — accept raw notes, persist, return note_id.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.models.note import Note
from app.models.user import User
from app.schemas.note import NoteUploadRequest, NoteUploadResponse
from app.core.exceptions import Note2MotionError
from app.core.logging import logger

router = APIRouter()


@router.post("/upload-notes", response_model=NoteUploadResponse)
async def upload_notes(payload: NoteUploadRequest, db: AsyncSession = Depends(get_db)):
    if len(payload.raw_text.strip()) < 10:
        raise Note2MotionError("Notes too short.", status_code=422)

    user_id = None
    if payload.user_email:
        result = await db.execute(select(User).where(User.email == payload.user_email))
        user = result.scalar_one_or_none()
        if not user:
            user = User(email=payload.user_email)
            db.add(user)
            await db.flush()
        user_id = user.id

    note = Note(
        user_id=user_id,
        title=payload.title,
        raw_text=payload.raw_text,
        source=payload.source,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    logger.info(f"📥 Uploaded note {note.id} ({len(note.raw_text)} chars)")
    return NoteUploadResponse(
        note_id=note.id,
        title=note.title,
        char_count=len(note.raw_text),
        message="Note uploaded successfully.",
    )