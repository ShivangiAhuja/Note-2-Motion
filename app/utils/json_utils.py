"""
Safe JSON parsing utilities. LLMs sometimes wrap JSON in code fences or add prose.
"""

import json
import re
from typing import Any


def extract_json(text: str) -> Any:
    """
    Extract JSON from arbitrary LLM text.
    Tries direct parse → fenced block → first {...}/[...] match.
    """
    if not text:
        raise ValueError("Empty LLM response")

    # 1. Direct
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. ```json ... ``` fenced
    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        try:
            return json.loads(fence.group(1))
        except Exception:
            pass

    # 3. First {...} or [...] greedy match
    for pattern in (r"\{.*\}", r"\[.*\]"):
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                continue

    raise ValueError(f"Could not parse JSON from LLM output:\n{text[:500]}")