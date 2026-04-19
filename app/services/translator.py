"""
Step 5 — Multilingual translation (en, hi, hinglish).
"""

import json
import asyncio
from typing import List, Dict, Any

from app.services.llm_client import llm_client
from app.services.prompts import TRANSLATION_PROMPT
from app.utils.json_utils import extract_json
from app.core.exceptions import PipelineError
from app.core.logging import logger


async def _translate_single(
    language: str, concepts: List[Dict[str, Any]], quizzes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    payload = {"concepts": concepts, "quizzes": quizzes}
    prompt = TRANSLATION_PROMPT.format(
        language=language,
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    raw = await llm_client.complete(prompt, system="Return strict JSON.")
    try:
        return extract_json(raw)
    except Exception as e:
        raise PipelineError(f"Translation to {language} failed: {e}")


async def translate_content(
    languages: List[str],
    concepts: List[Dict[str, Any]],
    quizzes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    logger.info(f"Translating into: {languages}")
    results = await asyncio.gather(
        *[_translate_single(lang, concepts, quizzes) for lang in languages],
        return_exceptions=True,
    )
    bundles = []
    for lang, res in zip(languages, results):
        if isinstance(res, Exception):
            logger.warning(f"Translation failed for {lang}: {res}")
            continue
        bundles.append(res)
    return bundles