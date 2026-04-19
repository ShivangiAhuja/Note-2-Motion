"""
Prompt templates for every pipeline step.
Each prompt demands STRICT JSON output so downstream parsing is reliable.
"""

CONCEPT_EXTRACTION_PROMPT = """You are an expert study-notes analyzer.

TASK:
Extract the key learning concepts from the notes below.

RULES:
- Output STRICT JSON ONLY. No prose, no markdown fences.
- Each concept must be atomic and teachable on its own.
- 3 to 8 concepts.

SCHEMA:
{{
  "concepts": [
    {{
      "id": "c1",
      "title": "string",
      "summary": "2-4 sentence explanation",
      "keywords": ["..."],
      "difficulty": "easy|medium|hard"
    }}
  ]
}}

NOTES:
\"\"\"{notes}\"\"\"
"""

SCENE_PLANNING_PROMPT = """You are an educational animator planning short explainer animations.

TASK:
For each concept, design a scene-based animation plan (3-6 steps per scene).

RULES:
- Output STRICT JSON ONLY.
- Each step must contain narration + visual description + duration (seconds).
- Total scene duration between 20 and 60 seconds.

SCHEMA:
{{
  "scenes": [
    {{
      "scene_id": "s1",
      "concept_id": "c1",
      "title": "string",
      "steps": [
        {{
          "step_id": 1,
          "narration": "what the narrator says",
          "visual": "what appears on screen",
          "duration_sec": 5.0,
          "animation_hint": "fade-in | zoom | draw | highlight | etc."
        }}
      ]
    }}
  ]
}}

CONCEPTS:
{concepts_json}
"""

QUIZ_GENERATION_PROMPT = """You are a quiz designer creating MCQs from study concepts.

TASK:
Generate exactly {num_quizzes} multiple-choice questions covering the concepts.

RULES:
- Output STRICT JSON ONLY.
- Each MCQ must have 4 options and ONE correct answer.
- Include a brief explanation for the correct answer.
- Vary difficulty across easy, medium, hard.

SCHEMA:
{{
  "quizzes": [
    {{
      "question": "string",
      "options": ["a","b","c","d"],
      "correct_index": 0,
      "explanation": "string",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}

CONCEPTS:
{concepts_json}
"""

TRANSLATION_PROMPT = """You are a multilingual education translator.

TASK:
Translate the given concepts and quizzes into: {language}.

RULES:
- Output STRICT JSON ONLY.
- Preserve structure and IDs.
- For "hinglish", use romanized Hindi mixed with English naturally (conversational).
- For "hi", use Devanagari Hindi.
- For "en", clean, clear English.

SCHEMA:
{{
  "language": "{language}",
  "concepts": [ /* same schema as input concepts */ ],
  "quizzes":  [ /* same schema as input quizzes  */ ]
}}

INPUT:
{payload_json}
"""

VALIDATION_PROMPT = """You are a strict QA reviewer for educational AI output.

TASK:
Review the pipeline output for correctness, completeness, and pedagogical quality.

CHECK:
- Do concepts match the source notes?
- Are scenes logically sequenced?
- Are quiz answers correct and unambiguous?
- Are translations faithful?

RULES:
- Output STRICT JSON ONLY.

SCHEMA:
{{
  "passed": true,
  "score": 0.0-1.0,
  "issues": ["list of problems, empty if none"]
}}

NOTES:
\"\"\"{notes}\"\"\"

PIPELINE_OUTPUT:
{pipeline_json}
"""