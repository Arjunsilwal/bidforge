"""
Health Check and System Status Route.
"""
from fastapi import APIRouter
from api.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Returns application health and configuration metadata."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "api_version": "v1.0.0",
    }
