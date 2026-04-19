"""
GET /results/{id} — fetch pipeline output.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.models.generated_content import GeneratedContent
from app.models.quiz import Quiz
from app.schemas.generation import ResultResponse
from app.core.exceptions import Note2MotionError

router = APIRouter()


@router.get("/results/{generated_content_id}", response_model=ResultResponse)
async def get_results(generated_content_id: str, db: AsyncSession = Depends(get_db)):
    gc = await db.get(GeneratedContent, generated_content_id)
    if not gc:
        raise Note2MotionError("Generated content not found.", status_code=404)

    quizzes_q = await db.execute(
        select(Quiz).where(Quiz.generated_content_id == gc.id)
    )
    quizzes = quizzes_q.scalars().all()

    return ResultResponse(
        id=gc.id,
        note_id=gc.note_id,
        status=gc.status,
        error_message=gc.error_message,
        concepts=(gc.concepts or {}).get("items") if gc.concepts else None,
        scene_plan=(gc.scene_plan or {}).get("scenes") if gc.scene_plan else None,
        quizzes=[
            {
                "question": q.question,
                "options": q.options,
                "correct_index": q.correct_index,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
            }
            for q in quizzes
        ] or None,
        translations=(gc.translations or {}).get("bundles") if gc.translations else None,
        validation_report=gc.validation_report,
    )