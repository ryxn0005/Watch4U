"""Health check endpoint — used by Docker healthcheck and uptime monitors."""
from fastapi import APIRouter, Request

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    settings = get_settings()
    out: dict[str, str] = {"status": "ok", "service": "watch4u-backend"}
    if not settings.surreal_url.strip():
        out["surrealdb"] = "disabled"
    elif getattr(request.app.state, "surreal", None) is None:
        out["surrealdb"] = "unavailable"
    else:
        db = request.app.state.surreal
        try:
            out["surrealdb"] = "ok"
            out["surrealdb_version"] = str(await db.version())
        except Exception:
            out["surrealdb"] = "error"
    return out
