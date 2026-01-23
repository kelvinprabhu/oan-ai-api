"""
FastAPI Main Application

This is the entry point for the MahaVistaar AI API FastAPI application.
"""
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import chat_router, suggestions_router, transcribe_router, tts_router
from app.routers.health import router as health_router
from app.core.cache import cache
from helpers.utils import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up MahaVistaar AI API...")
    
    # Cache connection check moved to background to prevent startup blocking
    async def check_cache():
        try:
            await cache.set("health_check", "ok", ttl=60)
            logger.info("Cache connection successful")
        except Exception as e:
            logger.warning(f"Cache connection failed: {str(e)}")

    import asyncio
    asyncio.create_task(check_cache())
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MahaVistaar AI API...")
    logger.info("Application shutdown complete")

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered agricultural assistant API for Maharashtra farmers",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.allowed_credentials,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )
    
    # Include routers
    app.include_router(chat_router, prefix=settings.api_prefix)
    app.include_router(suggestions_router, prefix=settings.api_prefix)
    app.include_router(transcribe_router, prefix=settings.api_prefix)
    app.include_router(tts_router, prefix=settings.api_prefix)
    app.include_router(health_router, prefix=settings.api_prefix)
    
    @app.get("/")
    async def root():
        logger.info("ROOT endpoint hit")
        return {"status": "ok", "app": "MahaVistaar AI API"}
    
    # Azure Function host internal endpoints to stop 404 noise in logs
    # include_in_schema=False avoids duplicate Operation ID warnings and hides internal routes
    @app.post("/admin/host/synctriggers", include_in_schema=False)
    @app.get("/admin/host/synctriggers", include_in_schema=False)
    async def azure_sync_triggers():
        return {"status": "success"}

    @app.get("/admin/functions", include_in_schema=False)
    @app.get("/admin/functions/", include_in_schema=False)
    async def azure_get_functions():
        # Returns an empty list to satisfy Azure Function host's check
        return []

    @app.api_route("/admin/host/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=False)
    async def azure_host_proxy(path: str):
        return {"status": "ok", "path": path}
    
    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} server...")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.uvicorn_workers,
        log_level=settings.log_level.lower()
    )
