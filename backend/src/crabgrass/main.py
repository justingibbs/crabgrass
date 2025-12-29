"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crabgrass.config import get_settings
from crabgrass.database import init_schema, close_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    print("Starting Crabgrass API...")
    init_schema()
    print("Database schema initialized")

    yield

    # Shutdown
    print("Shutting down Crabgrass API...")
    close_connection()
    print("Database connection closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Crabgrass API",
        description="Idea-to-innovation platform with AI agents",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Register all API routes."""

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "crabgrass-api",
            "version": "0.1.0",
        }

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to Crabgrass API",
            "docs": "/docs",
            "health": "/health",
        }

    # TODO: Register API routers
    # app.include_router(ideas_router, prefix="/api/ideas", tags=["ideas"])
    # app.include_router(agent_router, prefix="/api/agent", tags=["agent"])


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "crabgrass.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
