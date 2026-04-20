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
        logger.debug(f"LLM provider={self.provider} | prompt chars={len(prompt)}")

        try:
            if self.provider == "mock":
                result = self._mock_response(prompt)
            elif self.provider == "openai":
                result = await self._openai(prompt, system, temperature)
            elif self.provider == "anthropic":
                result = await self._anthropic(prompt, system, temperature)
            elif self.provider == "groq":
                result = await self._groq(prompt, system, temperature)
            else:
                raise LLMError(f"Unknown LLM provider: {self.provider}")
            
            # Simple JSON validation check if system prompt mentions JSON
            if system and "json" in system.lower():
                from app.utils.json_utils import extract_json
                extract_json(result) # Validate it parses correctly
                
            return result
        except Exception as e:
            logger.warning(f"LLM complete failed (retrying): {e}")
            raise LLMError(f"LLM completion failed: {e}")

    async def _groq(self, prompt: str, system: Optional[str], temperature: float) -> str:
        """Groq — OpenAI-compatible, fast, free tier available."""
        if not settings.GROQ_API_KEY:
            raise LLMError("GROQ_API_KEY missing in environment.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                },
            )
        if r.status_code >= 400:
            raise LLMError(f"Groq error {r.status_code}: {r.text}")
        return r.json()["choices"][0]["message"]["content"]

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
                        "summary": "Plants convert sunlight, water, and CO2 into glucose and oxygen using chlorophyll, the green pigment found in leaves.",
                        "keywords": ["chlorophyll", "sunlight", "glucose", "oxygen", "CO2"],
                        "difficulty": "easy",
                    },
                    {
                        "id": "c2",
                        "title": "Light-dependent Reactions",
                        "summary": "These reactions occur in the thylakoid membranes of chloroplasts. They split water molecules and produce ATP and NADPH using sunlight energy.",
                        "keywords": ["thylakoid", "ATP", "NADPH", "water"],
                        "difficulty": "medium",
                    },
                    {
                        "id": "c3",
                        "title": "Calvin Cycle",
                        "summary": "Also known as the light-independent reactions, this cycle takes place in the stroma and uses ATP and NADPH to convert CO2 into glucose.",
                        "keywords": ["Calvin cycle", "stroma", "glucose", "CO2 fixation"],
                        "difficulty": "hard",
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
                            {"step_id": 1, "narration": "A green plant stands tall in bright sunlight.", "visual": "🌱 Plant with ☀️ sun overhead", "duration_sec": 4.0, "animation_hint": "fade-in"},
                            {"step_id": 2, "narration": "Water travels up from the roots through the stem.", "visual": "💧 Blue water droplets rising up the stem", "duration_sec": 5.0, "animation_hint": "draw"},
                            {"step_id": 3, "narration": "Carbon dioxide enters through tiny pores in the leaves.", "visual": "💨 CO₂ molecules flowing into leaves", "duration_sec": 5.0, "animation_hint": "particles"},
                            {"step_id": 4, "narration": "Glucose and oxygen are produced as outputs.", "visual": "🍬 Glucose + 💨 O₂ leaving the leaf", "duration_sec": 6.0, "animation_hint": "highlight"},
                        ],
                    },
                    {
                        "scene_id": "s2",
                        "concept_id": "c2",
                        "title": "Light-Dependent Reactions",
                        "steps": [
                            {"step_id": 1, "narration": "Inside the chloroplast, light hits the thylakoid membrane.", "visual": "☀️ Light rays striking 🟢 thylakoid disks", "duration_sec": 4.5, "animation_hint": "zoom"},
                            {"step_id": 2, "narration": "Water molecules are split into hydrogen and oxygen.", "visual": "💧 H₂O → H⁺ + ½O₂", "duration_sec": 5.0, "animation_hint": "split"},
                            {"step_id": 3, "narration": "ATP and NADPH are produced as energy carriers.", "visual": "⚡ ATP and NADPH molecules forming", "duration_sec": 5.5, "animation_hint": "build"},
                        ],
                    },
                    {
                        "scene_id": "s3",
                        "concept_id": "c3",
                        "title": "The Calvin Cycle",
                        "steps": [
                            {"step_id": 1, "narration": "In the stroma, the Calvin cycle begins.", "visual": "🔄 Cycle diagram in stroma", "duration_sec": 4.0, "animation_hint": "rotate"},
                            {"step_id": 2, "narration": "CO₂ is captured and combined with a 5-carbon sugar.", "visual": "💨 CO₂ + 🔵 RuBP → 6C compound", "duration_sec": 5.0, "animation_hint": "merge"},
                            {"step_id": 3, "narration": "Using ATP and NADPH, glucose is finally created.", "visual": "⚡ + 🍬 Glucose formed", "duration_sec": 6.0, "animation_hint": "celebrate"},
                        ],
                    }
                ]
            })

        if "generate exactly" in p and "multiple-choice" in p:
            return json.dumps({
                "quizzes": [
                    {
                        "question": "Which pigment is primarily responsible for photosynthesis?",
                        "options": ["Hemoglobin", "Chlorophyll", "Melanin", "Carotene"],
                        "correct_index": 1,
                        "explanation": "Chlorophyll is the green pigment in chloroplasts that absorbs light energy to drive photosynthesis.",
                        "difficulty": "easy",
                    },
                    {
                        "question": "Where do light-dependent reactions occur?",
                        "options": ["Stroma", "Nucleus", "Thylakoid membranes", "Mitochondria"],
                        "correct_index": 2,
                        "explanation": "Thylakoid membranes inside chloroplasts house photosystems I and II where light-dependent reactions happen.",
                        "difficulty": "medium",
                    },
                    {
                        "question": "What are the products of photosynthesis?",
                        "options": ["CO₂ and water", "Glucose and oxygen", "ATP and water", "Nitrogen and oxygen"],
                        "correct_index": 1,
                        "explanation": "Photosynthesis converts CO₂ and water into glucose (food) and oxygen using sunlight.",
                        "difficulty": "easy",
                    },
                    {
                        "question": "Which molecule is split during the light reactions?",
                        "options": ["Glucose", "Water", "Carbon dioxide", "ATP"],
                        "correct_index": 1,
                        "explanation": "Water is split (photolysis) to release electrons, protons, and oxygen during light reactions.",
                        "difficulty": "medium",
                    },
                    {
                        "question": "The Calvin cycle takes place in which part of the chloroplast?",
                        "options": ["Thylakoid", "Stroma", "Outer membrane", "Granum"],
                        "correct_index": 1,
                        "explanation": "The Calvin cycle (light-independent reactions) occurs in the stroma — the fluid surrounding thylakoids.",
                        "difficulty": "hard",
                    },
                ]
            })

        if "translate the given concepts" in p:
            # Detect language from prompt
            if "hinglish" in p:
                return json.dumps({
                    "language": "hinglish",
                    "concepts": [
                        {"id": "c1", "title": "Photosynthesis ka Overview", "summary": "Plants sunlight, paani aur CO2 ka use karke chlorophyll ki madad se glucose aur oxygen banate hain. Ye green pigment leaves mein hota hai.", "keywords": ["chlorophyll", "sunlight", "glucose"], "difficulty": "easy"},
                        {"id": "c2", "title": "Light-dependent Reactions", "summary": "Ye reactions thylakoid membrane mein hoti hain. Yahan water molecules todi jaati hain aur ATP aur NADPH banti hai sunlight ki energy se.", "keywords": ["thylakoid", "ATP", "NADPH"], "difficulty": "medium"},
                        {"id": "c3", "title": "Calvin Cycle", "summary": "Isko light-independent reactions bhi kehte hain. Ye stroma mein hota hai aur ATP aur NADPH ka use karke CO2 ko glucose mein convert karta hai.", "keywords": ["Calvin cycle", "stroma"], "difficulty": "hard"},
                    ],
                    "quizzes": [
                        {"question": "Photosynthesis ke liye kaun sa pigment zaroori hai?", "options": ["Hemoglobin", "Chlorophyll", "Melanin", "Carotene"], "correct_index": 1, "explanation": "Chlorophyll green pigment hai jo light energy ko absorb karta hai.", "difficulty": "easy"},
                        {"question": "Light-dependent reactions kahan hoti hain?", "options": ["Stroma", "Nucleus", "Thylakoid membranes", "Mitochondria"], "correct_index": 2, "explanation": "Thylakoid membranes mein photosystems I aur II hote hain.", "difficulty": "medium"},
                        {"question": "Photosynthesis ke products kya hain?", "options": ["CO₂ aur paani", "Glucose aur oxygen", "ATP aur paani", "Nitrogen aur oxygen"], "correct_index": 1, "explanation": "Photosynthesis se glucose aur oxygen banta hai.", "difficulty": "easy"},
                        {"question": "Light reactions mein kaunsa molecule split hota hai?", "options": ["Glucose", "Water", "Carbon dioxide", "ATP"], "correct_index": 1, "explanation": "Water split hota hai (photolysis) aur oxygen release hota hai.", "difficulty": "medium"},
                        {"question": "Calvin cycle chloroplast ke kis part mein hota hai?", "options": ["Thylakoid", "Stroma", "Outer membrane", "Granum"], "correct_index": 1, "explanation": "Calvin cycle stroma mein hota hai.", "difficulty": "hard"},
                    ],
                })
            elif '"hi"' in prompt or "devanagari" in p:
                return json.dumps({
                    "language": "hi",
                    "concepts": [
                        {"id": "c1", "title": "प्रकाश संश्लेषण का अवलोकन", "summary": "पौधे सूर्य के प्रकाश, पानी और कार्बन डाइऑक्साइड का उपयोग करके क्लोरोफिल की सहायता से ग्लूकोज और ऑक्सीजन बनाते हैं। यह हरा वर्णक पत्तियों में होता है।", "keywords": ["क्लोरोफिल", "सूर्य प्रकाश", "ग्लूकोज"], "difficulty": "easy"},
                        {"id": "c2", "title": "प्रकाश-निर्भर अभिक्रियाएँ", "summary": "ये अभिक्रियाएँ थायलाकोइड झिल्ली में होती हैं। यहाँ पानी के अणु टूटते हैं और सूर्य के प्रकाश की ऊर्जा से ATP और NADPH बनते हैं।", "keywords": ["थायलाकोइड", "ATP", "NADPH"], "difficulty": "medium"},
                        {"id": "c3", "title": "कैल्विन चक्र", "summary": "इसे प्रकाश-स्वतंत्र अभिक्रियाएँ भी कहा जाता है। यह स्ट्रोमा में होता है और ATP तथा NADPH का उपयोग करके CO2 को ग्लूकोज में बदलता है।", "keywords": ["कैल्विन चक्र", "स्ट्रोमा"], "difficulty": "hard"},
                    ],
                    "quizzes": [
                        {"question": "प्रकाश संश्लेषण के लिए कौन सा वर्णक मुख्य रूप से जिम्मेदार है?", "options": ["हीमोग्लोबिन", "क्लोरोफिल", "मेलेनिन", "कैरोटीन"], "correct_index": 1, "explanation": "क्लोरोफिल हरा वर्णक है जो प्रकाश ऊर्जा को अवशोषित करता है।", "difficulty": "easy"},
                        {"question": "प्रकाश-निर्भर अभिक्रियाएँ कहाँ होती हैं?", "options": ["स्ट्रोमा", "नाभिक", "थायलाकोइड झिल्ली", "माइटोकॉन्ड्रिया"], "correct_index": 2, "explanation": "थायलाकोइड झिल्ली में फोटोसिस्टम I और II होते हैं।", "difficulty": "medium"},
                        {"question": "प्रकाश संश्लेषण के उत्पाद क्या हैं?", "options": ["CO₂ और पानी", "ग्लूकोज और ऑक्सीजन", "ATP और पानी", "नाइट्रोजन और ऑक्सीजन"], "correct_index": 1, "explanation": "प्रकाश संश्लेषण से ग्लूकोज और ऑक्सीजन बनते हैं।", "difficulty": "easy"},
                        {"question": "प्रकाश अभिक्रियाओं के दौरान कौन सा अणु विभाजित होता है?", "options": ["ग्लूकोज", "पानी", "कार्बन डाइऑक्साइड", "ATP"], "correct_index": 1, "explanation": "पानी विभाजित होता है (प्रकाश अपघटन) और ऑक्सीजन निकलती है।", "difficulty": "medium"},
                        {"question": "कैल्विन चक्र क्लोरोप्लास्ट के किस भाग में होता है?", "options": ["थायलाकोइड", "स्ट्रोमा", "बाहरी झिल्ली", "ग्रेनम"], "correct_index": 1, "explanation": "कैल्विन चक्र स्ट्रोमा में होता है।", "difficulty": "hard"},
                    ],
                })
            else:
                # English
                return json.dumps({
                    "language": "en",
                    "concepts": [
                        {"id": "c1", "title": "Photosynthesis Overview", "summary": "Plants convert sunlight, water, and CO2 into glucose and oxygen using chlorophyll, the green pigment found in leaves.", "keywords": ["chlorophyll", "sunlight", "glucose"], "difficulty": "easy"},
                        {"id": "c2", "title": "Light-dependent Reactions", "summary": "These reactions occur in the thylakoid membranes. They split water molecules and produce ATP and NADPH using sunlight energy.", "keywords": ["thylakoid", "ATP", "NADPH"], "difficulty": "medium"},
                        {"id": "c3", "title": "Calvin Cycle", "summary": "Also known as the light-independent reactions, this cycle takes place in the stroma and uses ATP and NADPH to convert CO2 into glucose.", "keywords": ["Calvin cycle", "stroma"], "difficulty": "hard"},
                    ],
                    "quizzes": [
                        {"question": "Which pigment is primarily responsible for photosynthesis?", "options": ["Hemoglobin", "Chlorophyll", "Melanin", "Carotene"], "correct_index": 1, "explanation": "Chlorophyll is the green pigment that absorbs light energy.", "difficulty": "easy"},
                        {"question": "Where do the light-dependent reactions occur?", "options": ["Stroma", "Nucleus", "Thylakoid membranes", "Mitochondria"], "correct_index": 2, "explanation": "Thylakoid membranes house photosystems I and II.", "difficulty": "medium"},
                        {"question": "What are the products of photosynthesis?", "options": ["CO₂ and water", "Glucose and oxygen", "ATP and water", "Nitrogen and oxygen"], "correct_index": 1, "explanation": "Photosynthesis produces glucose and oxygen.", "difficulty": "easy"},
                        {"question": "Which molecule is split during the light reactions?", "options": ["Glucose", "Water", "Carbon dioxide", "ATP"], "correct_index": 1, "explanation": "Water is split (photolysis), releasing oxygen.", "difficulty": "medium"},
                        {"question": "The Calvin cycle takes place in which part of the chloroplast?", "options": ["Thylakoid", "Stroma", "Outer membrane", "Granum"], "correct_index": 1, "explanation": "The Calvin cycle occurs in the stroma.", "difficulty": "hard"},
                    ],
                })

        if "strict qa reviewer" in p:
            return json.dumps({"passed": True, "score": 0.92, "issues": []})

        # default
        return json.dumps({"ok": True})


llm_client = LLMClient()