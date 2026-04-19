"""
POST /generate-content — kicks off async pipeline for a note.
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.note import Note
from app.models.generated_content import GeneratedContent
from app.schemas.generation import GenerateRequest, GenerateResponse
from app.services.pipeline import run_pipeline
from app.core.exceptions import Note2MotionError
from app.core.logging import logger

router = APIRouter()


@router.post("/generate-content", response_model=GenerateResponse)
async def generate_content(
    payload: GenerateRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    note = await db.get(Note, payload.note_id)
    if not note:
        raise Note2MotionError("Note not found.", status_code=404)

    gc = GeneratedContent(note_id=note.id, status="pending")
    db.add(gc)
    await db.commit()
    await db.refresh(gc)

    # Kick off async pipeline (FastAPI BackgroundTasks)
    background.add_task(
        run_pipeline,
        generated_content_id=gc.id,
        note_id=note.id,
        languages=payload.languages,
        num_quizzes=payload.num_quizzes,
    )

    logger.info(f"🧠 Pipeline queued for note {note.id} -> gc {gc.id}")
    return GenerateResponse(
        generated_content_id=gc.id,
        status=gc.status,
        message="Generation started. Poll /api/results/{id} for updates.",
    )