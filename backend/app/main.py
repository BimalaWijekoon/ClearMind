"""
ClearMind — FastAPI Application Entry Point

Initializes the FastAPI app with CORS, lifespan management (DB + Redis),
router registration, and WebSocket mounting.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.api.routes import router as api_router
from app.api.websocket import router as ws_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("clearmind")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown tasks."""
    settings = get_settings()
    logger.info("🧠 ClearMind starting up...")

    # Initialize database tables
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization skipped: {e}")

    # Test Redis connection
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis not available: {e}")

    # Check Gemini API key
    if settings.google_api_key and settings.google_api_key != "your_gemini_api_key_here":
        logger.info("✅ Gemini API key configured")
    else:
        logger.warning("⚠️ Gemini API key not set — agent pipeline will not work")

    logger.info(f"🚀 ClearMind v{settings.app_version} ready")
    yield
    logger.info("🧠 ClearMind shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="AI Metacognition Engine — Detects and Corrects Cognitive Biases in LLM Outputs",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(api_router, prefix="/api")
    app.include_router(ws_router)

    @app.get("/health", tags=["System"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
        }

    return app


# Create the app instance
app = create_app()
