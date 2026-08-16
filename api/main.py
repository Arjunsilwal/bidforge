"""
BidForge FastAPI Application Entrypoint.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.database import Base, engine
from api.routes.estimates import router as estimates_router
from api.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown events."""
    # Create SQLite/Postgres tables on startup if not already created
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="AI Preconstruction Estimating Engine - Turning bid packages into defensible, traceable draft estimates.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(estimates_router)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} v1 API",
        "docs_url": "/docs",
        "health_url": "/health",
    }
