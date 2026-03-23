from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(_api_key_header)):
    """Dependency that enforces X-API-Key header on all protected routes."""
    if not settings.api_key:
        # API key protection disabled (e.g. during local dev without key set)
        return
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
