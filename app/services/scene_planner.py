"""
Step 3 — Scene Planning.
"""

import json
from typing import List, Dict, Any

from app.services.llm_client import llm_client
from app.services.prompts import SCENE_PLANNING_PROMPT
from app.utils.json_utils import extract_json
from app.core.exceptions import PipelineError
from app.core.logging import logger


async def plan_scenes(concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    prompt = SCENE_PLANNING_PROMPT.format(concepts_json=json.dumps(concepts, ensure_ascii=False))
    raw = await llm_client.complete(prompt, system="Return strict JSON.")
    try:
        data = extract_json(raw)
        scenes = data.get("scenes", [])
        logger.info(f"Planned {len(scenes)} scenes")
        return scenes
    except Exception as e:
        raise PipelineError(f"Scene planning failed: {e}")