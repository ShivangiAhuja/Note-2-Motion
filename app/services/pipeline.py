"""
Orchestrates the full Note2Motion pipeline:
preprocess → concepts → scenes → quizzes → translations → validate
Persists results to DB. Safe for background execution.
"""

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.core.config import settings

from app.models.generated_content import GeneratedContent
from app.models.note import Note
from app.models.quiz import Quiz

from app.services.preprocessing import preprocess_notes
from app.services.concept_extractor import extract_concepts
from app.services.scene_planner import plan_scenes
from app.services.quiz_generator import generate_quizzes
from app.services.translator import translate_content
from app.services.validator import validate_pipeline


async def _update_status(session: AsyncSession, gc: GeneratedContent, status: str, error: str | None = None):
    gc.status = status
    gc.error_message = error
    gc.updated_at = datetime.utcnow()
    await session.commit()


async def run_pipeline(
    generated_content_id: str,
    note_id: str,
    languages: list[str] | None,
    num_quizzes: int,
) -> None:
    """
    Background task. Opens its own DB session (never reuses a request session).
    """
    languages = languages or settings.default_languages_list
    async with AsyncSessionLocal() as session:
        gc = await session.get(GeneratedContent, generated_content_id)
        note = await session.get(Note, note_id)
        if not gc or not note:
            logger.error(f"Pipeline aborted: missing records gc={generated_content_id} note={note_id}")
            return

        try:
            await _update_status(session, gc, "processing")

            # 1. Preprocess
            clean_notes = preprocess_notes(note.raw_text)
            logger.info(f"[{gc.id}] Preprocessed notes ({len(clean_notes)} chars)")

            # 2. Concepts
            concepts = await extract_concepts(clean_notes)

            # 3. Scenes
            scenes = await plan_scenes(concepts)

            # 4. Quizzes
            quizzes = await generate_quizzes(concepts, num_quizzes=num_quizzes)

            # 5. Translations
            translations = await translate_content(languages, concepts, quizzes)

            # 6. Validation
            report = await validate_pipeline(clean_notes, concepts, scenes, quizzes)

            # Persist JSON blobs
            gc.concepts = {"items": concepts}
            gc.scene_plan = {"scenes": scenes}
            gc.translations = {"bundles": translations}
            gc.validation_report = report

            # Persist quizzes into normalized table as well
            for q in quizzes:
                session.add(Quiz(
                    generated_content_id=gc.id,
                    question=q["question"],
                    options=q["options"],
                    correct_index=q["correct_index"],
                    explanation=q.get("explanation"),
                    difficulty=q.get("difficulty", "medium"),
                ))

            gc.status = "completed"
            gc.updated_at = datetime.utcnow()
            await session.commit()
            logger.info(f"[{gc.id}] ✅ Pipeline completed")

        except Exception as e:
            logger.exception(f"[{gc.id}] ❌ Pipeline failed: {e}")
            await _update_status(session, gc, "failed", str(e))