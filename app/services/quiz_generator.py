"""
Step 4 — Quiz generation.
"""

import json
from typing import List, Dict, Any

from app.services.llm_client import llm_client
from app.services.prompts import QUIZ_GENERATION_PROMPT
from app.utils.json_utils import extract_json
from app.core.exceptions import PipelineError
from app.core.logging import logger


async def generate_quizzes(concepts: List[Dict[str, Any]], num_quizzes: int = 5) -> List[Dict[str, Any]]:
    prompt = QUIZ_GENERATION_PROMPT.format(
        num_quizzes=num_quizzes,
        concepts_json=json.dumps(concepts, ensure_ascii=False),
    )
    raw = await llm_client.complete(prompt, system="Return strict JSON.")
    try:
        data = extract_json(raw)
        quizzes = data.get("quizzes", [])
        # Sanity filter
        quizzes = [q for q in quizzes if self_validate_quiz(q)]
        logger.info(f"Generated {len(quizzes)} quizzes")
        return quizzes
    except Exception as e:
        raise PipelineError(f"Quiz generation failed: {e}")


def self_validate_quiz(q: Dict[str, Any]) -> bool:
    try:
        return (
            isinstance(q.get("question"), str)
            and isinstance(q.get("options"), list)
            and len(q["options"]) == 4
            and isinstance(q.get("correct_index"), int)
            and 0 <= q["correct_index"] < 4
        )
    except Exception:
        return False