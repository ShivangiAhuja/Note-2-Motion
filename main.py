"""
Note2Motion — FastAPI entry point.
Starts the API server, initializes DB, and mounts routers.
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, dispose_db
from app.core.logging import setup_logging, logger
from app.core.exceptions import register_exception_handlers
from app.api.routes import notes, generation, results


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifecycle — create tables on startup, dispose engine on shutdown."""
    setup_logging()
    logger.info("🚀 Starting Note2Motion backend...")
    await init_db()
    logger.info("✅ Database initialized")
    yield
    await dispose_db()
    logger.info("🛑 Backend shut down cleanly")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Convert study notes into concepts, scene plans, quizzes, and multilingual explanations.",
    lifespan=lifespan,
)

# CORS — open for local dev; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Routers
app.include_router(notes.router, prefix="/api", tags=["Notes"])
app.include_router(generation.router, prefix="/api", tags=["Generation"])
app.include_router(results.router, prefix="/api", tags=["Results"])


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "ok",
        "env": settings.APP_ENV,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_ENV == "development",
    )