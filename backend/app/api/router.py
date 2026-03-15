from fastapi import APIRouter

from .health import router as health_router
from .subtitles import router as subtitles_router
from .annotations import router as annotations_router
from .flashcards import router as flashcards_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router, tags=["health"])
api_router.include_router(subtitles_router, tags=["subtitles"])
api_router.include_router(annotations_router, tags=["annotations"])
api_router.include_router(flashcards_router, tags=["flashcards"])
