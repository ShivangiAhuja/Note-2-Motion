"""
Step 2 — Concept Extraction.
"""

from typing import List, Dict, Any

from app.services.llm_client import llm_client
from app.services.prompts import CONCEPT_EXTRACTION_PROMPT
from app.utils.json_utils import extract_json
from app.core.exceptions import PipelineError
from app.core.logging import logger


async def extract_concepts(notes: str) -> List[Dict[str, Any]]:
    prompt = CONCEPT_EXTRACTION_PROMPT.format(notes=notes)
    raw = await llm_client.complete(prompt, system="Return strict JSON.")
    try:
        data = extract_json(raw)
        concepts = data.get("concepts", [])
        if not concepts:
            raise PipelineError("No concepts extracted.")
        logger.info(f"Extracted {len(concepts)} concepts")
        return concepts
    except Exception as e:
        raise PipelineError(f"Concept extraction failed: {e}")