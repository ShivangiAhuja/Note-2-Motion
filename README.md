# Note2Motion — Backend

Convert study notes into **structured concepts**, **scene-based animation plans**, **interactive quizzes**, and **multilingual explanations** (English, Hindi, Hinglish).

Built with **FastAPI + async SQLAlchemy + PostgreSQL**. LLM-agnostic — runs locally in `mock` mode and plugs into OpenAI or Anthropic with a single env var.

---

## 🚀 Setup

### 1. Clone & install
```bash
git clone <your-repo>
cd note2motion

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database
Use any PostgreSQL instance — local, **Supabase**, or **Neon**.

```bash
# Local Docker option:
docker run --name n2m-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16
createdb -h localhost -U postgres note2motion
```

Supabase/Neon: copy the async connection string in the form:
```
postgresql+asyncpg://USER:PASS@HOST:PORT/DB
```

### 3. Environment
```bash
cp .env.example .env
# edit .env — set DATABASE_URL, and LLM_PROVIDER (mock | openai | anthropic)
```

### 4. Run the server
```bash
python main.py
# OR
uvicorn main:app --reload --port 8000
```

Server: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

---

## 🧠 LLM Configuration

Edit `.env`:

| Provider | Env Vars |
|---------|---------|
| `mock` (default) | none — returns deterministic fake JSON |
| `openai` | `OPENAI_API_KEY`, `OPENAI_MODEL` |
| `anthropic` | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` |

Then set:
```env
LLM_PROVIDER=openai
```

---

## 🧪 Testing the API

### 1. Upload notes
```bash
curl -X POST http://localhost:8000/api/upload-notes \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "test@example.com",
    "title": "Photosynthesis",
    "raw_text": "Photosynthesis is the process by which plants make food from sunlight, water, and carbon dioxide..."
  }'
```
Response:
```json
{"note_id": "uuid-...", "title": "Photosynthesis", "char_count": 117, "message": "Note uploaded successfully."}
```

### 2. Generate content
```bash
curl -X POST http://localhost:8000/api/generate-content \
  -H "Content-Type: application/json" \
  -d '{"note_id": "<uuid-from-step-1>", "num_quizzes": 5, "languages": ["en","hi","hinglish"]}'
```

### 3. Fetch results (poll until `status = completed`)
```bash
curl http://localhost:8000/api/results/<generated_content_id>
```

---

## 🧩 Pipeline (all modular)

```
preprocessing → concept_extractor → scene_planner → quiz_generator → translator → validator
```

Every step is:
- A separate file under `app/services/`
- Uses a dedicated prompt in `app/services/prompts.py`
- Emits **strict JSON**
- Independently testable

---

## 🗄️ Database Schema

- `users` — optional user tracking
- `notes` — raw uploaded notes
- `generated_content` — pipeline outputs (JSON blobs + status)
- `quizzes` — normalized quiz rows (for fast retrieval + analytics)

For production migrations, integrate Alembic (already in requirements).

---

## 🛠 Extending

- **Plug a new LLM** → add a method in `app/services/llm_client.py` and route it via `LLM_PROVIDER`.
- **Add a pipeline step** → create `app/services/<step>.py`, add a prompt, insert it into `app/services/pipeline.py`.
- **Swap background runner** → `BackgroundTasks` works for dev; move to Celery / Arq / RQ for scale.
- **Frontend / Antigravity** → consume the REST endpoints directly. Schema is stable.

---

## 📂 Folder Map

```
app/
  api/         # FastAPI routes
  services/    # AI pipeline modules + prompts + LLM client
  models/      # SQLAlchemy models
  schemas/     # Pydantic schemas
  core/        # config, database, logging, exceptions
  utils/       # json & text helpers
main.py
```

---

## ✅ Status Codes

| Endpoint | Success | Failure |
|---------|---------|--------|
| `POST /api/upload-notes` | 200 | 422 (short), 500 |
| `POST /api/generate-content` | 200 | 404 (note), 500 |
| `GET /api/results/{id}` | 200 | 404 |

---

Happy building 🚀