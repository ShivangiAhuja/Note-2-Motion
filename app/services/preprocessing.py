"""
Step 1 — Input preprocessing.
Cleans and truncates raw notes before feeding into LLM.
"""

from app.core.config import settings
from app.utils.text_utils import normalize_whitespace, truncate


def preprocess_notes(raw_text: str) -> str:
    cleaned = normalize_whitespace(raw_text)
    return truncate(cleaned, settings.MAX_NOTE_CHARS)