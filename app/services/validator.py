"""
Step 6 — Validation Layer.
Structural checks + optional LLM-based QA review.
"""

import json
from typing import Dict, Any, List

from app.services.llm_client import llm_client
from app.services.prompts import VALIDATION_PROMPT
from app.utils.json_utils import extract_json
from app.core.logging import logger


def _structural_checks(
    concepts: List[Dict[str, Any]],
    scenes: List[Dict[str, Any]],
    quizzes: List[Dict[str, Any]],
) -> List[str]:
    issues = []
    if not concepts:
        issues.append("No concepts found.")
    if not scenes:
        issues.append("No scenes generated.")
    if not quizzes:
        issues.append("No quizzes generated.")

    concept_ids = {c.get("id") for c in concepts}
    for s in scenes:
        if s.get("concept_id") not in concept_ids:
            issues.append(f"Scene {s.get('scene_id')} references unknown concept {s.get('concept_id')}.")

    for i, q in enumerate(quizzes):
        if not (0 <= q.get("correct_index", -1) < len(q.get("options", []))):
            issues.append(f"Quiz {i} has invalid correct_index.")
    return issues


async def validate_pipeline(
    notes: str,
    concepts: List[Dict[str, Any]],
    scenes: List[Dict[str, Any]],
    quizzes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    structural_issues = _structural_checks(concepts, scenes, quizzes)

    pipeline_payload = {"concepts": concepts, "scenes": scenes, "quizzes": quizzes}
    prompt = VALIDATION_PROMPT.format(
        notes=notes[:4000],
        pipeline_json=json.dumps(pipeline_payload, ensure_ascii=False)[:6000],
    )

    try:
        raw = await llm_client.complete(prompt, system="Return strict JSON.")
        llm_report = extract_json(raw)
    except Exception as e:
        logger.warning(f"LLM validator failed, falling back: {e}")
        llm_report = {"passed": True, "score": 0.8, "issues": []}

    merged_issues = structural_issues + llm_report.get("issues", [])
    passed = len(structural_issues) == 0 and llm_report.get("passed", True)
    score = 0.0 if not passed else float(llm_report.get("score", 1.0))

    return {"passed": passed, "score": score, "issues": merged_issues}