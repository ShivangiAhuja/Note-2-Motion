"""
LLM Client abstraction.
Supports: mock (default), openai, anthropic.
Plug your API key in .env and switch LLM_PROVIDER.
"""

import json
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import LLMError


class LLMClient:
    """Unified async LLM interface."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def complete(self, prompt: str, system: Optional[str] = None, temperature: float = 0.2) -> str:
        """
        Returns raw string response from the underlying LLM.
        Callers are expected to extract JSON via utils.json_utils.extract_json.
        """
        logger.debug(f"LLM provider={self.provider} | prompt chars={len(prompt)}")

        if self.provider == "mock":
            return self._mock_response(prompt)
        if self.provider == "openai":
            return await self._openai(prompt, system, temperature)
        if self.provider == "anthropic":
            return await self._anthropic(prompt, system, temperature)

        raise LLMError(f"Unknown LLM provider: {self.provider}")

    # ---------------- Providers ----------------

    async def _openai(self, prompt: str, system: Optional[str], temperature: float) -> str:
        if not settings.OPENAI_API_KEY:
            raise LLMError("OPENAI_API_KEY missing in environment.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                },
            )
        if r.status_code >= 400:
            raise LLMError(f"OpenAI error {r.status_code}: {r.text}")
        return r.json()["choices"][0]["message"]["content"]

    async def _anthropic(self, prompt: str, system: Optional[str], temperature: float) -> str:
        if not settings.ANTHROPIC_API_KEY:
            raise LLMError("ANTHROPIC_API_KEY missing in environment.")

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.ANTHROPIC_MODEL,
                    "max_tokens": 4096,
                    "temperature": temperature,
                    "system": system or "You are a helpful assistant that returns strict JSON.",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        if r.status_code >= 400:
            raise LLMError(f"Anthropic error {r.status_code}: {r.text}")
        data = r.json()
        return data["content"][0]["text"]

    # ---------------- Mock ----------------

    def _mock_response(self, prompt: str) -> str:
        """
        Deterministic mock for local development & CI.
        Returns plausible JSON based on which prompt was sent.
        """
        p = prompt.lower()

        if "extract the key learning concepts" in p:
            return json.dumps({
                "concepts": [
                    {
                        "id": "c1",
                        "title": "Photosynthesis Overview",
                        "summary": "Plants convert sunlight, water, and CO2 into glucose and oxygen using chlorophyll.",
                        "keywords": ["chlorophyll", "sunlight", "glucose", "oxygen"],
                        "difficulty": "easy",
                    },
                    {
                        "id": "c2",
                        "title": "Light-dependent Reactions",
                        "summary": "Occur in thylakoid membranes; split water and produce ATP and NADPH.",
                        "keywords": ["thylakoid", "ATP", "NADPH"],
                        "difficulty": "medium",
                    },
                ]
            })

        if "design a scene-based animation plan" in p:
            return json.dumps({
                "scenes": [
                    {
                        "scene_id": "s1",
                        "concept_id": "c1",
                        "title": "How Plants Make Food",
                        "steps": [
                            {"step_id": 1, "narration": "A plant stands in sunlight.", "visual": "Plant + sun icon", "duration_sec": 4.0, "animation_hint": "fade-in"},
                            {"step_id": 2, "narration": "Water rises from roots.", "visual": "Blue arrows up stem", "duration_sec": 5.0, "animation_hint": "draw"},
                            {"step_id": 3, "narration": "CO2 enters leaves.", "visual": "Gray particles into leaf", "duration_sec": 5.0, "animation_hint": "particles"},
                            {"step_id": 4, "narration": "Glucose and O2 are produced.", "visual": "Molecules leaving leaf", "duration_sec": 6.0, "animation_hint": "highlight"},
                        ],
                    }
                ]
            })

        if "generate exactly" in p and "multiple-choice" in p:
            return json.dumps({
                "quizzes": [
                    {
                        "question": "Which pigment drives photosynthesis?",
                        "options": ["Hemoglobin", "Chlorophyll", "Melanin", "Carotene"],
                        "correct_index": 1,
                        "explanation": "Chlorophyll absorbs light energy in chloroplasts.",
                        "difficulty": "easy",
                    },
                    {
                        "question": "Where do light-dependent reactions occur?",
                        "options": ["Stroma", "Nucleus", "Thylakoid membranes", "Mitochondria"],
                        "correct_index": 2,
                        "explanation": "Thylakoid membranes house photosystems I and II.",
                        "difficulty": "medium",
                    },
                ]
            })

        if "translate the given concepts" in p:
            # naive passthrough for mock
            if "hinglish" in p:
                lang = "hinglish"
            elif "\"hi\"" in p or "devanagari" in p:
                lang = "hi"
            else:
                lang = "en"
            return json.dumps({
                "language": lang,
                "concepts": [{"id": "c1", "title": f"[{lang}] Photosynthesis", "summary": f"[{lang}] summary", "keywords": [], "difficulty": "easy"}],
                "quizzes":  [{"question": f"[{lang}] Q1", "options": ["a","b","c","d"], "correct_index": 0, "explanation": "", "difficulty": "easy"}],
            })

        if "strict qa reviewer" in p:
            return json.dumps({"passed": True, "score": 0.92, "issues": []})

        # default
        return json.dumps({"ok": True})


llm_client = LLMClient()