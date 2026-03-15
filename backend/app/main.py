import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.router import api_router
from .config import settings
from .db import init_db

# ── Logging setup ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)-30s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
# Quiet down noisy libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger("app.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Anime Subtitle Companion — starting up")
    logger.info("=" * 60)
    logger.info(f"LLM endpoint:  {settings.LLM_API_BASE}")
    logger.info(f"LLM model:     {settings.LLM_MODEL}")
    logger.info(f"LLM max tokens:{settings.LLM_MAX_TOKENS}")
    logger.info(f"SearXNG:       {settings.SEARXNG_URL or '(not configured)'}")
    logger.info(f"Database:      {settings.DATABASE_PATH}")
    logger.info("-" * 60)
    await init_db()
    logger.info("Database initialized")
    logger.info("Ready to serve requests")
    yield
    logger.info("Shutting down")


app = FastAPI(title="Anime Subtitle Companion", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# In production, serve the built frontend
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
