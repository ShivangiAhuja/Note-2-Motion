"""Schemas for content generation & results."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class GenerateRequest(BaseModel):
    note_id: str
    languages: Optional[List[str]] = Field(
        default=None,
        description="Languages to translate into. Defaults to env-provided list.",
    )
    num_quizzes: int = Field(5, ge=1, le=20)


class GenerateResponse(BaseModel):
    generated_content_id: str
    status: str
    message: str


# ---------- Pipeline structured outputs ----------

class Concept(BaseModel):
    id: str
    title: str
    summary: str
    keywords: List[str]
    difficulty: str  # easy | medium | hard


class SceneStep(BaseModel):
    step_id: int
    narration: str
    visual: str
    duration_sec: float
    animation_hint: Optional[str] = None


class Scene(BaseModel):
    scene_id: str
    concept_id: str
    title: str
    steps: List[SceneStep]


class QuizItem(BaseModel):
    question: str
    options: List[str]
    correct_index: int
    explanation: Optional[str] = None
    difficulty: str = "medium"


class TranslationBundle(BaseModel):
    language: str
    concepts: List[Dict[str, Any]]
    quizzes: List[Dict[str, Any]]


class ValidationReport(BaseModel):
    passed: bool
    issues: List[str] = []
    score: float = 1.0


class ResultResponse(BaseModel):
    id: str
    note_id: str
    status: str
    error_message: Optional[str]
    concepts: Optional[List[Concept]] = None
    scene_plan: Optional[List[Scene]] = None
    quizzes: Optional[List[QuizItem]] = None
    translations: Optional[List[TranslationBundle]] = None
    validation_report: Optional[ValidationReport] = None